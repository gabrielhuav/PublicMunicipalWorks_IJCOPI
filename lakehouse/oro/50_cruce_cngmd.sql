-- Dos fuentes oficiales sobre 2022: lo que cada municipio declaró a INEGI en contratos
-- de obra pública y lo que SHCP registra como contratos de obra convocados por un
-- municipio. Una diferencia no prueba irregularidad: el CNGMD cuenta lo que el municipio
-- reporta sobre todos sus recursos y SHCP solo ve el gasto federalizado.
-- Un contrato puede vincularse a varios folios: contar y sumar al mismo grano.
-- Si un identificador trae varios montos, se conserva el máximo informado; no
-- equivale a un pago acreditado ni se puede inferir aquí cuál fue el último monto.
WITH contratos_municipales AS (
    SELECT o.cvemun, coalesce(c.id_contrato, c.numero_contrato) AS contrato,
           max(c.monto) AS monto
    FROM plata_contratos c
    JOIN oro_proyecto_ciclo o USING (folio, ciclo)
    WHERE c.ciclo = 2022 AND c.tipo_contratacion = 'Obra'
      AND (c.convocante ILIKE '%MUNICIPI%' OR c.convocante ILIKE '%AYUNTAMIENTO%')
      AND coalesce(c.id_contrato, c.numero_contrato) IS NOT NULL
    GROUP BY o.cvemun, coalesce(c.id_contrato, c.numero_contrato)
), shcp AS (
    SELECT cvemun, count(*) AS contratos_shcp, sum(monto) AS monto_shcp
    FROM contratos_municipales
    GROUP BY cvemun
)
SELECT m.cvemun, m.entidad, m.municipio, m.pobtot,
       n.contratos_total AS contratos_cngmd, n.monto_total AS monto_cngmd,
       coalesce(s.contratos_shcp, 0) AS contratos_shcp, s.monto_shcp,
       CASE WHEN n.contratos_total IS NULL THEN 'sin dato en CNGMD'
            WHEN n.contratos_total = 0 AND coalesce(s.contratos_shcp, 0) > 0
                 THEN 'CNGMD en cero, SHCP con contratos'
            WHEN n.contratos_total > 0 AND coalesce(s.contratos_shcp, 0) = 0
                 THEN 'CNGMD con contratos, SHCP en cero'
            WHEN n.contratos_total = 0 THEN 'ambas en cero'
            WHEN s.contratos_shcp > n.contratos_total THEN 'SHCP mayor que CNGMD'
            ELSE 'CNGMD mayor o igual que SHCP' END AS relacion
FROM plata_municipios m
LEFT JOIN plata_cngmd_contratos n ON n.cvemun = m.cvemun AND n.materia = 2
LEFT JOIN shcp s ON s.cvemun = m.cvemun
