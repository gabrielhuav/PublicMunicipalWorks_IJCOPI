-- Contratos de obra de 2022 según dos fuentes oficiales: lo que cada municipio declaró a INEGI
-- en el CNGMD 2023 y lo que SHCP registra como contratos de obra convocados por un municipio.
-- Una diferencia no prueba irregularidad: el CNGMD cubre todos los recursos del municipio y
-- SHCP solo el gasto federalizado.
-- monto_shcp suma una vez cada identificador por municipio, tomando su máximo
-- monto informado si difiere entre folios; no representa gasto pagado acreditado.
SELECT cvemun, contratos_cngmd, monto_cngmd, contratos_shcp, monto_shcp, relacion
FROM oro_cruce_cngmd
ORDER BY cvemun;
