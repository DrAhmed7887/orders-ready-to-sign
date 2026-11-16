-- S3 · Función renal que cae en silencio → grupo 1 «Empeorando».
-- ≥3 FGe que abarcan ≥12 meses con pendiente < −5 ml/min/1,73 m²/año (mínimos cuadrados),
-- o paso a peor categoría G con caída ≥25 % desde el primer valor (KDIGO 2012, rec. 2.1.3).
-- S3c · caída aislada >20 % entre los dos últimos valores, sin tendencia: «repetir analítica» (KDIGO 2024, PP 2.1.3).

-- Vuelta 13 (Ahmed, 16 nov 2026), R3: la serie usa solo la ecuación del último valor (KDIGO 2024, PP 1.2.4.1).
CREATE TEMP TABLE s3_serie AS
SELECT f.person_id, f.fecha, f.valor,
       (julianday(f.fecha) - julianday(ref.hoy)) / 365.25 AS x,
       CASE WHEN f.valor >= 90 THEN 1 WHEN f.valor >= 60 THEN 2 WHEN f.valor >= 45 THEN 3
            WHEN f.valor >= 30 THEN 4 WHEN f.valor >= 15 THEN 5 ELSE 6 END AS cat   -- G1, G2, G3a, G3b, G4, G5
FROM fge f CROSS JOIN ref
JOIN fge_ultimo u ON u.person_id = f.person_id AND u.codigo = f.codigo
WHERE f.fecha >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_ventana_fge') || ' months')
  AND f.person_id NOT IN (SELECT person_id FROM fge_invalido);   -- con una unidad o un valor dudoso no se calcula tendencia

-- FGe con unidad no aceptada o valor imposible: no se puede decidir → registro, nunca aviso.
INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT i.person_id, 'S3', 1, 0, 'FGe', i.problema, 'Revisar el FGe', '', i.fecha,
       'Información insuficiente: ' || i.problema
FROM fge_invalido i;

-- R3: si en la ventana hay valores de otra ecuación y los de la ecuación del último valor no bastan para una
-- tendencia (≥3 valores que abarcan ≥12 meses), no se calcula: registro, nunca aviso.
INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT f.person_id, 'S3', 1, 0, 'FGe', 'FGe de distintas ecuaciones en los últimos 36 meses', 'Revisar el FGe', '',
       MAX(f.fecha),
       'Información insuficiente: FGe de distintas ecuaciones (MDRD, CKD-EPI); no se calcula la tendencia'
FROM fge f CROSS JOIN ref
WHERE f.fecha >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_ventana_fge') || ' months')
  AND f.person_id NOT IN (SELECT person_id FROM fge_invalido)
GROUP BY f.person_id
HAVING COUNT(DISTINCT f.codigo) > 1
   -- solo si, mezclando ecuaciones, habría habido tendencia: con pocos valores no hay nada que avisar
   AND COUNT(DISTINCT f.fecha) >= 3
   AND MAX(f.fecha) >= date(MIN(f.fecha), '+' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_min_tendencia') || ' months')
   AND f.person_id NOT IN (SELECT person_id FROM s3_serie GROUP BY person_id
                           HAVING COUNT(*) >= 3
                              AND MAX(fecha) >= date(MIN(fecha), '+' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_min_tendencia') || ' months'));

CREATE TEMP TABLE s3_tendencia AS
SELECT a.person_id, a.n, a.f0, a.f1, a.pendiente,
       primero.valor AS v0, primero.cat AS cat0, ultimo.valor AS v1, ultimo.cat AS cat1
FROM (
  SELECT person_id, COUNT(*) AS n, MIN(fecha) AS f0, MAX(fecha) AS f1,
         (COUNT(*) * SUM(x * valor) - SUM(x) * SUM(valor)) / NULLIF(COUNT(*) * SUM(x * x) - SUM(x) * SUM(x), 0) AS pendiente
  FROM s3_serie GROUP BY person_id
) a
JOIN s3_serie primero ON primero.person_id = a.person_id AND primero.fecha = a.f0
JOIN s3_serie ultimo  ON ultimo.person_id  = a.person_id AND ultimo.fecha  = a.f1;

CREATE TEMP VIEW s3_disparo AS
SELECT t.*,
       t.n >= 3
       AND t.f1 >= date(t.f0, '+' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_min_tendencia') || ' months')
       AND (t.pendiente < (SELECT valor FROM parametro WHERE clave = 'pendiente_fge')
            OR (t.cat1 > t.cat0 AND t.v1 <= t.v0 * (1 - (SELECT valor FROM parametro WHERE clave = 'caida_categoria_pct') / 100.0)))
       AS tendencia
FROM s3_tendencia t;

INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, prueba_extra, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT d.person_id, 'S3', 1, -d.pendiente, 'FGe', 'CAC',
       'FGe ' || CAST(ROUND(d.v0) AS INTEGER) || ' → ' || CAST(ROUND(d.v1) AS INTEGER) ||
         ' (' || d.f0 || ' a ' || d.f1 || ', ' || d.n || ' valores): ' ||
         printf('%.1f', d.pendiente) || ' ml/min/1,73 m²/año' ||
         CASE WHEN d.cat1 > d.cat0
                   AND d.v1 <= d.v0 * (1 - (SELECT valor FROM parametro WHERE clave = 'caida_categoria_pct') / 100.0)
              THEN '; paso de ' || (SELECT g FROM (SELECT 1 k, 'G1' g UNION ALL SELECT 2, 'G2' UNION ALL SELECT 3, 'G3a'
                                                   UNION ALL SELECT 4, 'G3b' UNION ALL SELECT 5, 'G4' UNION ALL SELECT 6, 'G5') WHERE k = d.cat0)
                   || ' → ' || (SELECT g FROM (SELECT 1 k, 'G1' g UNION ALL SELECT 2, 'G2' UNION ALL SELECT 3, 'G3a'
                                                   UNION ALL SELECT 4, 'G3b' UNION ALL SELECT 5, 'G4' UNION ALL SELECT 6, 'G5') WHERE k = d.cat1)
                   || ' con caída de ' || CAST(ROUND(100.0 * (d.v0 - d.v1) / d.v0) AS INTEGER) || ' %'
              ELSE '' END,
       'Función renal en descenso: repetir FGe + CAC, valorar',
       'Descenso de FGe (KDIGO 2012, rec. 2.1.3): se solicita FGe y CAC.',
       d.f1,
       NULL
FROM s3_disparo d
WHERE d.tendencia;

-- S3c: caída aislada >20 % entre los dos últimos valores, cuando no hay tendencia.
INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT ult.person_id, 'S3c', 1, -100, 'FGe',
       'FGe ' || CAST(ROUND(ant.valor) AS INTEGER) || ' (' || ant.fecha || ') → ' ||
         CAST(ROUND(ult.valor) AS INTEGER) || ' (' || ult.fecha || '): cambio de ' ||
         CAST(ROUND(100.0 * (ant.valor - ult.valor) / ant.valor) AS INTEGER) || ' %',
       'Cambio >20 %: repetir analítica',
       'Caída de FGe >20 % (KDIGO 2024, PP 2.1.3): se repite la analítica.',
       ult.fecha,
       NULL
FROM (SELECT person_id, fecha, valor, ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY fecha DESC) AS rn FROM s3_serie) ult
JOIN (SELECT person_id, fecha, valor, ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY fecha DESC) AS rn FROM s3_serie) ant
  ON ant.person_id = ult.person_id AND ult.rn = 1 AND ant.rn = 2
WHERE ult.valor < ant.valor * (1 - (SELECT valor FROM parametro WHERE clave = 'caida_aislada_pct') / 100.0)
  AND ult.person_id NOT IN (SELECT person_id FROM s3_disparo WHERE tendencia);
