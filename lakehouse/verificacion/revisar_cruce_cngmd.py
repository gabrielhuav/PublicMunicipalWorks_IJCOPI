"""Reproduce la capa 04 desde tres ZIP oficiales, sin PostgreSQL, S3 ni Iceberg.

Usa las conversiones de plata.py y los SQL reales de oro/50 y capas/04. Verifica
los SHA-256 de las fuentes antes de leerlas. Por defecto solo comprueba la salida;
--actualizar escribe exclusivamente la capa 04 y su entrada del manifiesto.
--evidencia permite conservar un informe nuevo sin sobrescribir mediciones antiguas.

Ejemplo: python lakehouse/verificacion/revisar_cruce_cngmd.py --bronce lakehouse/datos/bronce
"""
import argparse
import ast
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import duckdb
import pandas as pd
import pyarrow as pa
from jsonschema import Draft4Validator, FormatChecker
from referencing import Registry, Resource

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "etl"))
from plata import leer_csv, a_tabla, PROYECTOS, CONTRATOS, MUNICIPIOS, CNGMD  # noqa: E402
from exportar_capas import canonico, plano, texto  # noqa: E402

ORO = RAIZ / "oro/50_cruce_cngmd.sql"
CAPA = RAIZ / "capas/04_cruce_cngmd_2022.duck.sql"
SALIDA = RAIZ / "sitio/datos/04_cruce_cngmd_2022.json"
MANIFIESTO = RAIZ / "sitio/datos/manifiesto.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def registros(con, sql):
    cur = con.execute(sql)
    return [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]


def vistas_fuente(con, rutas):
    """Solo columnas que consume oro/50; mismas conversiones que la carga plata."""
    with ZipFile(rutas["shcp_ef2022"]) as z:
        base = "ef2022/cuarto_informe_definitivo/"
        p, _ = leer_csv(z, base + "ef2022.csv", ("FOLIO", "CICLO", "TRIMESTRE",
                           "ID_ENTIDAD_FEDERATIVA", "ID_MUNICIPIO_RESPONSABLE"))
        p = p.rename(columns={"FOLIO": "folio", "CICLO": "ciclo", "TRIMESTRE": "periodo",
                              "ID_ENTIDAD_FEDERATIVA": "id_entidad", "ID_MUNICIPIO_RESPONSABLE": "id_municipio"})
        campos = ("folio", "ciclo", "periodo", "id_entidad", "id_municipio")
        con.register("proyectos_fuente", a_tabla(p, pa.schema([PROYECTOS.field(k) for k in campos]), {}))
        con.execute("""CREATE TABLE oro_proyecto_ciclo AS SELECT folio, ciclo,
            lpad(id_entidad::VARCHAR, 2, '0') || lpad(id_municipio::VARCHAR, 3, '0') AS cvemun
            FROM proyectos_fuente QUALIFY row_number() OVER
            (PARTITION BY folio, ciclo ORDER BY periodo DESC) = 1""")
        c, _ = leer_csv(z, base + "contratos.csv", ("FOLIO", "TIPO_OBRA", "ID_CONTRATO_ADMINISTRACION",
                                                    "CONVOCANTE", "MONTO"))
        c = c.rename(columns={"FOLIO": "folio", "TIPO_OBRA": "tipo_contratacion",
                               "ID_CONTRATO_ADMINISTRACION": "id_contrato", "CONVOCANTE": "convocante", "MONTO": "monto"})
        c["ciclo"] = "2022"
        campos = ("folio", "ciclo", "tipo_contratacion", "id_contrato", "numero_contrato", "convocante", "monto")
        con.register("plata_contratos", a_tabla(c, pa.schema([CONTRATOS.field(k) for k in campos]), {}))
    with ZipFile(rutas["inegi_iter2020"]) as z:
        member = next(n for n in z.namelist() if n.endswith(".csv") and "conjunto" in n)
        m, _ = leer_csv(z, member, ("ENTIDAD", "MUN", "LOC", "NOM_ENT", "NOM_MUN", "POBTOT"), "utf-8-sig")
        m = m[(m.MUN != "000") & (m.LOC == "0000")].copy()
        m["cvemun"] = m.ENTIDAD + m.MUN
        m = m.rename(columns={"NOM_ENT": "entidad", "NOM_MUN": "municipio", "POBTOT": "pobtot"})
        campos = ("cvemun", "entidad", "municipio", "pobtot")
        con.register("plata_municipios", a_tabla(m, pa.schema([MUNICIPIOS.field(k) for k in campos]), {}))
    with ZipFile(rutas["inegi_cngmd2023"]) as z:
        a, _ = leer_csv(z, "conjunto_de_datos/m2s8p8_cngmd2023.csv", codificacion="latin-1")
        b, _ = leer_csv(z, "conjunto_de_datos/m2s8p9_cngmd2023.csv", codificacion="latin-1")
        a = pd.DataFrame({"cvemun": a.UBICAGEO_F.str.zfill(5), "materia": a.TIMATERI_E, "contratos_total": a.PRORIGTT})
        b = pd.DataFrame({"cvemun": b.UBICAGEO_F.str.zfill(5), "materia": b.TIMATERI_E, "monto_total": b.PRORIGTT})
        n = a.merge(b, how="left", on=["cvemun", "materia"]).replace("NA", "")
        campos = ("cvemun", "materia", "contratos_total", "monto_total")
        con.register("plata_cngmd_contratos", a_tabla(n, pa.schema([CNGMD.field(k) for k in campos]), {}))


def probar_sql():
    """Regresión: mismo ID multificolio, importes distintos e igualdad entre IDs."""
    con = duckdb.connect()
    con.execute("""CREATE TABLE oro_proyecto_ciclo AS SELECT * FROM (VALUES
        ('a',2022,'01001'),('b',2022,'01001'),('c',2022,'01002')) t(folio,ciclo,cvemun);
        CREATE TABLE plata_municipios AS SELECT * FROM (VALUES
        ('01001','A','Uno',10),('01002','A','Dos',20)) t(cvemun,entidad,municipio,pobtot);
        CREATE TABLE plata_cngmd_contratos(cvemun VARCHAR,materia INTEGER,contratos_total BIGINT,monto_total DECIMAL(20,2));
        CREATE TABLE plata_contratos AS SELECT * FROM (VALUES
        ('a',2022,'Obra','X',NULL,'MUNICIPIO',100.00),
        ('b',2022,'Obra','X',NULL,'MUNICIPIO',120.00),
        ('b',2022,'Obra','Y',NULL,'MUNICIPIO',120.00),
        ('b',2022,'Obra',NULL,'N','AYUNTAMIENTO',60.00),
        ('b',2022,'Obra',NULL,NULL,'MUNICIPIO',55.00),
        ('c',2022,'Obra','X',NULL,'MUNICIPIO',80.00),
        ('b',2021,'Obra','Z',NULL,'MUNICIPIO',999.00),
        ('b',2022,'Servicio','Z',NULL,'MUNICIPIO',999.00))
        t(folio,ciclo,tipo_contratacion,id_contrato,numero_contrato,convocante,monto)""")
    con.execute("CREATE VIEW oro_cruce_cngmd AS " + ORO.read_text(encoding="utf-8"))
    actual = con.execute("SELECT cvemun,contratos_shcp,monto_shcp FROM oro_cruce_cngmd ORDER BY cvemun").fetchall()
    assert [(a, b, float(c)) for a, b, c in actual] == [("01001", 3, 300.0), ("01002", 1, 80.0)]
    con.close()


def probar_paquete():
    """Valida el metadato realmente generado, sin volver a medir la proyección."""
    path = RAIZ / "proyecciones/oc4ids.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "paquete" for t in n.targets))
    date = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "CONSULTADO" for t in n.targets))
    data = eval(compile(ast.Expression(package), str(path), "eval"), {"__builtins__": {}},
                {"CONSULTADO": date, "resultado": [{"id": "fixture-research-project"}]})
    directory = RAIZ / "proyecciones/esquema"
    project = json.loads((directory / "project-schema.json").read_text(encoding="utf-8"))
    schema = json.loads((directory / "project-package-schema.json").read_text(encoding="utf-8"))
    registry = Registry().with_resource(project["id"], Resource.from_contents(project))
    errors = list(Draft4Validator(schema, registry=registry, format_checker=FormatChecker()).iter_errors(data))
    assert not errors, [e.message for e in errors]
    assert data["uri"] == "https://github.com/gabrielhuav/PublicMunicipalWorks_IJCOPI"
    return {"uri": data["uri"], "fixture_schema_errors": len(errors), "full_export_rerun": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bronce", type=Path, default=RAIZ / "datos/bronce")
    parser.add_argument("--actualizar", action="store_true")
    parser.add_argument("--evidencia", type=Path)
    parser.add_argument("--solo-pruebas", action="store_true")
    args = parser.parse_args()
    probar_sql()
    package = probar_paquete()
    if args.solo_pruebas:
        print(json.dumps({"sql_fixture_passed": True, "oc4ids_package": package}, indent=2))
        return 0
    manifest = json.loads((RAIZ / "fuentes.json").read_text(encoding="utf-8"))
    sources, rutas = {}, {}
    for source in manifest["fuentes"]:
        if source["id"] not in ("shcp_ef2022", "inegi_iter2020", "inegi_cngmd2023"):
            continue
        path = args.bronce / source["ruta_bronce"]
        actual = sha(path.read_bytes())
        assert actual == source["sha256"], source["id"]
        sources[source["id"]] = {"sha256": actual, "bytes": path.stat().st_size}
        rutas[source["id"]] = path
    con = duckdb.connect()
    vistas_fuente(con, rutas)
    con.execute("""CREATE VIEW alcance AS SELECT o.cvemun,c.* FROM plata_contratos c
        JOIN oro_proyecto_ciclo o USING(folio,ciclo)
        WHERE c.ciclo=2022 AND c.tipo_contratacion='Obra'
        AND(c.convocante ILIKE '%MUNICIPI%' OR c.convocante ILIKE '%AYUNTAMIENTO%')""")
    raw = registros(con, """SELECT count(*) AS filas,count(*) FILTER(WHERE coalesce(id_contrato,numero_contrato) IS NULL) AS sin_id,
        sum(monto) AS suma_filas FROM alcance""")[0]
    groups = registros(con, """SELECT count(*) AS contratos,sum(monto) AS suma_maximos,
        count(*) FILTER(WHERE folios>1) AS repetidos_multifolio,
        count(*) FILTER(WHERE montos>1) AS con_montos_distintos
        FROM(SELECT cvemun,coalesce(id_contrato,numero_contrato),max(monto) AS monto,
             count(DISTINCT folio) AS folios,count(DISTINCT monto) AS montos FROM alcance
             WHERE coalesce(id_contrato,numero_contrato) IS NOT NULL GROUP BY 1,2)""")[0]
    con.execute("CREATE VIEW oro_cruce_cngmd AS " + ORO.read_text(encoding="utf-8"))
    cur = con.execute(CAPA.read_text(encoding="utf-8"))
    columns = [d[0] for d in cur.description]
    rows = [[plano(v) for v in row] for row in cur.fetchall()]
    data = canonico(columns, rows)
    old = json.loads(SALIDA.read_text(encoding="utf-8"))
    assert old["columnas"] == columns and len(old["filas"]) == len(rows)
    index = columns.index("monto_shcp")
    changed = 0
    for before, after in zip(old["filas"], rows):
        assert before[:index] + before[index + 1:] == after[:index] + after[index + 1:], before[0]
        changed += before[index] != after[index]
    current_manifest = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    entry = next(q for q in current_manifest["consultas"] if q["consulta"] == CAPA.name)
    old_sha = sha(SALIDA.read_bytes())
    if args.actualizar:
        SALIDA.write_bytes(data)
        entry.update(sha256_consulta=sha(texto(CAPA)), sha256_datos=sha(data), sql=texto(CAPA).decode("utf-8"))
        entry["actualizado_en"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        # generado_en corresponde a la exportación histórica de todas las capas;
        # la revisión focalizada se fecha en su evidencia separada.
        MANIFIESTO.write_text(json.dumps(current_manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    else:
        assert SALIDA.read_bytes() == data, "La capa 04 difiere del SQL actual"
        assert entry["sha256_datos"] == sha(data) and entry["sha256_consulta"] == sha(texto(CAPA))
    result = {"generado_en": dt.datetime.now(dt.timezone.utc).isoformat(),
              "metodo": "SQL reales de oro/50 y capas/04 sobre conversiones de plata.py y tres ZIP con SHA-256 verificado; sin servicios",
              "alcance": "Solo capa 04; no se midieron ni actualizaron S3, PostgreSQL, Iceberg ni latencias históricas",
              "fuentes": sources, "antes_de_deduplicar": raw, "contratos_por_municipio": groups,
              "regla_monto": "Máximo monto informado por cvemun e identificador antes de sumar; no equivale a gasto pagado ni identifica el último valor",
              "capa": {"filas": len(rows), "columnas": columns, "sha256_sql_oro": sha(texto(ORO)),
                       "sha256_sql_capa": sha(texto(CAPA)), "sha256_datos": sha(data),
                       "actualizado_en": entry.get("actualizado_en")},
              "temascaltepec": registros(con, "SELECT * FROM oro_cruce_cngmd WHERE cvemun='15086'")[0],
              "sql_fixture_passed": True, "oc4ids_package": package}
    if args.actualizar:
        result["actualizacion"] = {"sha256_anterior": old_sha, "municipios_con_monto_corregido": changed,
                                  "otras_columnas_identicas": True}
    if args.evidencia:
        args.evidencia.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
