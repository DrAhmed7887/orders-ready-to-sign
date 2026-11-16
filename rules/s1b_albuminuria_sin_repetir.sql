-- S1b · Albuminuria que nadie repitió → grupo 2 «Sin seguimiento».
-- Último CAC ≥30 mg/g (o ≥3 mg/mmol), sin CAC posterior en >6 meses y sin código N18 (KDIGO 2024, tabla 1; PP 1.1.3.2).
-- El último CAC es el alterado: si hubiera uno posterior, ese sería el último.

INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT u.person_id, 'S1b', 2,
       CASE WHEN u.a3 THEN 1 ELSE 0 END,           -- A3 sale primero
       'CAC',
       'CAC ' || printf('%g', u.valor) || ' ' || u.unidad || ' (' || CASE WHEN u.a3 THEN 'A3' ELSE 'A2' END || ') el ' || u.fecha ||
         ', sin repetir en ' || CAST((julianday(ref.hoy) - julianday(u.fecha)) / 30.44 AS INTEGER) ||
         ' meses y sin código de ERC',
       'Albuminuria sin confirmar: repetir CAC en primera orina de la mañana',
       'CAC alterado sin confirmar (KDIGO 2024, PP 1.1.3.2 y 1.3.1.2): se solicita repetición en primera orina de la mañana (chorro medio); evitar durante la menstruación, tras ejercicio intenso o con infección urinaria sintomática o hematuria (tabla 16).',
       u.fecha,
       NULL
FROM cac_ultimo u
CROSS JOIN ref
WHERE u.alterado = 1
  AND u.fecha < date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_sin_repetir_cac') || ' months')
  AND u.person_id NOT IN (SELECT person_id FROM tiene_codigo WHERE grupo = 'ERC');

-- Último CAC sin resultado o con unidad desconocida: no se puede decidir → registro, nunca aviso.
INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT u.person_id, 'S1b', 2, 0, 'CAC',
       'CAC ' || CASE WHEN u.valor IS NULL THEN 'sin resultado' ELSE printf('%g', u.valor) END || ' el ' || u.fecha,
       'Revisar el último CAC', '', u.fecha,
       CASE WHEN u.valor IS NULL
            THEN 'Información insuficiente: el último CAC no tiene resultado numérico'
            WHEN u.valor < 0
            THEN 'Información insuficiente: CAC con valor imposible (' || printf('%g', u.valor) || ')'
            ELSE 'Información insuficiente: unidad del CAC desconocida («' || COALESCE(u.unidad, 'vacía') || '»)'
       END
FROM cac_ultimo u
WHERE u.alterado IS NULL
  AND u.person_id NOT IN (SELECT person_id FROM tiene_codigo WHERE grupo = 'ERC');

-- S1d · Albuminuria persistente en dos analíticas (vuelta 13, Ahmed, 16 nov 2026, R1) → grupo 2 «Sin seguimiento».
-- Último CAC alterado y otro CAC alterado de laboratorio ≥3 meses antes, sin ningún CAC normal entre los dos y sin
-- código de ERC: la cronicidad ya está probada (KDIGO 2024, PP 1.1.3.1: «review of past measurements of
-- albuminuria»). Sustituye a S1b para esa persona. Nunca propone un fármaco.
CREATE TEMP TABLE s1d AS
SELECT u.person_id, u.valor AS v1, u.unidad AS u1, u.fecha AS f1, a.valor AS v0, a.unidad AS u0, a.fecha AS f0
FROM cac_ultimo u
JOIN cac a ON a.person_id = u.person_id AND a.alterado = 1
          AND a.fecha <= date(u.fecha, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_persistencia_cac') || ' months')
WHERE u.alterado = 1
  AND u.person_id NOT IN (SELECT person_id FROM tiene_codigo WHERE grupo = 'ERC')
  AND NOT EXISTS (SELECT 1 FROM cac z WHERE z.person_id = u.person_id AND z.alterado = 0
                    AND z.fecha > a.fecha AND z.fecha < u.fecha)
  AND a.measurement_id = (SELECT a2.measurement_id FROM cac a2
                          WHERE a2.person_id = u.person_id AND a2.alterado = 1
                            AND a2.fecha <= date(u.fecha, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_persistencia_cac') || ' months')
                            AND NOT EXISTS (SELECT 1 FROM cac z2 WHERE z2.person_id = u.person_id AND z2.alterado = 0
                                              AND z2.fecha > a2.fecha AND z2.fecha < u.fecha)
                          ORDER BY a2.fecha DESC, a2.measurement_id LIMIT 1);

INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT s.person_id, 'S1d', 2, 2, 'ERC',
       'CAC ' || printf('%g', s.v0) || ' ' || s.u0 || ' (' || s.f0 || ') → ' || printf('%g', s.v1) || ' ' || s.u1 ||
         ' (' || s.f1 || '), sin CAC normal entre medias y sin código de ERC',
       'Albuminuria persistente en dos analíticas: valorar código de ERC (N18)',
       'Albuminuria en dos determinaciones de laboratorio separadas ≥3 meses (KDIGO 2024, PP 1.1.3.1): valorar diagnóstico de ERC.',
       s.f1,
       NULL
FROM s1d s;

DELETE FROM candidato WHERE regla = 'S1b' AND person_id IN (SELECT person_id FROM s1d);
