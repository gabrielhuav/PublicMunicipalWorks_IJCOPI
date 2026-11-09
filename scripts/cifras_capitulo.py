"""Mide las tres cifras del capítulo de ICOKG que la versión extendida corrige.

Requiere la pila de docker/compose.yml sembrada y con la API arriba:
    docker compose -f docker/compose.yml up -d db api
    python scripts/cifras_capitulo.py
    python scripts/cifras_capitulo.py --sin-api    conserva el tamaño de la API ya archivado

1. Habitantes de Temascaltepec: el capítulo dice 64,844. Sale de la capa 02_municipios del
   sitio del lago, que es el Censo 2020 (ITER) tal como lo devuelve la consulta.
2. Eventos de auditoría de una instancia sembrada: el capítulo dice "about 28,000". También
   se desglosan por origen, porque la suma no se explica con los votos solos: el generador
   escribe eventos de tipo al azar (que pueden caer en el tipo de voto) y uno más por voto,
   y los disparadores escriben el resto (obras, informes, costos, imágenes y votos).
3. Tamaño de la respuesta de /api/public/obras: el capítulo dice 753 kB. Con --sin-api no se
   vuelve a medir y se conserva el valor archivado en el JSON.
Escribe lakehouse/verificacion/cifras_capitulo.json.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

import psycopg2

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "lakehouse" / "verificacion" / "cifras_capitulo.json"
PG = os.environ.get("LAGO_PG", "postgresql://obras:obras_local@localhost:55432/obras_publicas")
API = os.environ.get("OBRAS_API", "http://localhost:5000")

# Las descripciones con que cada origen escribe sus eventos: generate_synthetic_data.py
# (generar_eventos_auditoria y generar_votos_propuestas) y db/arquitectura/FUNCIONES Y TRIGGERS.sql.
ORIGEN = """CASE WHEN f.descripcion_evento LIKE 'Evento % generado sint%' THEN 'generador_azar'
                 WHEN f.descripcion_evento LIKE 'Voto emitido por poblador %' THEN 'generador_por_voto'
                 ELSE 'disparadores' END"""


def main():
    capa = json.loads((RAIZ / "lakehouse/sitio/datos/02_municipios.json").read_text(encoding="utf-8"))
    fila = dict(zip(capa["columnas"], next(f for f in capa["filas"] if f[0] == "15086")))
    con = psycopg2.connect(PG)
    with con.cursor() as cur:
        cur.execute("""
            SELECT (SELECT count(*) FROM warehouse.fact_eventos_auditoria),
                   (SELECT count(*) FROM warehouse.fact_eventos_auditoria f
                    JOIN warehouse.dim_tipo_evento t USING (tipo_evento_key)
                    WHERE t.codigo_evento = 'VOTO_EMITIDO'),
                   (SELECT count(*) FROM public.votos_propuestas)""")
        eventos, eventos_voto, votos = cur.fetchone()
        cur.execute(f"SELECT {ORIGEN}, count(*) FROM warehouse.fact_eventos_auditoria f GROUP BY 1 ORDER BY 1")
        por_origen = dict(cur.fetchall())
        cur.execute(f"""
            SELECT t.codigo_evento, count(*) FROM warehouse.fact_eventos_auditoria f
            JOIN warehouse.dim_tipo_evento t USING (tipo_evento_key)
            WHERE {ORIGEN} = 'disparadores' GROUP BY 1 ORDER BY 2 DESC""")
        disparadores = dict(cur.fetchall())
        cur.execute(f"""
            SELECT {ORIGEN}, count(*) FROM warehouse.fact_eventos_auditoria f
            JOIN warehouse.dim_tipo_evento t USING (tipo_evento_key)
            WHERE t.codigo_evento = 'VOTO_EMITIDO' GROUP BY 1 ORDER BY 1""")
        voto_por_origen = dict(cur.fetchall())
    con.close()
    assert sum(por_origen.values()) == eventos and sum(voto_por_origen.values()) == eventos_voto

    if "--sin-api" in sys.argv:
        api = json.loads(SALIDA.read_text(encoding="utf-8"))["api_public_obras"]
    else:
        with urllib.request.urlopen(f"{API}/api/public/obras") as r:
            api = {"bytes": len(r.read()), "capitulo": "753 kB"}
    salida = {
        "temascaltepec": {"cvemun": "15086", "pobtot_censo_2020": fila["pobtot"],
                          "fuente": "lakehouse/sitio/datos/02_municipios.json", "capitulo": 64844},
        "eventos_auditoria": {"total": eventos, "de_voto": eventos_voto, "votos": votos,
                              "capitulo": "about 28,000", "por_origen": por_origen,
                              "disparadores_por_tipo": disparadores,
                              "de_voto_por_origen": voto_por_origen},
        "api_public_obras": api,
    }
    SALIDA.write_text(
        json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
