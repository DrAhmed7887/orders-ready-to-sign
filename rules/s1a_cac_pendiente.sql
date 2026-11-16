-- S1a · Cribado que nunca se pidió → grupo 3 «Prueba pendiente».
-- DM2 / HTA / FGe <60 sin ningún CAC en los últimos 12 meses (PROT-AP ERC 2025).
-- Si S1b ya pide repetir un CAC alterado, ese pedido cubre el cribado: no se pide un segundo CAC (corre después de S1b).

INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT p.person_id, 'S1a', 3, 0, 'CAC',
       CASE WHEN u.fecha IS NULL
            THEN 'Sin ningún CAC registrado'
            ELSE 'Último CAC el ' || u.fecha || ' (' ||
                 CAST((julianday(ref.hoy) - julianday(u.fecha)) / 30.44 AS INTEGER) || ' meses)'
       END,
       'Solicitar CAC',
       'Cribado anual de ERC (PROT-AP ERC 2025): se solicita CAC.',
       u.fecha,
       NULL
FROM poblacion p
CROSS JOIN ref
LEFT JOIN cac_ultimo u ON u.person_id = p.person_id
WHERE (u.fecha IS NULL
       OR u.fecha < date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_sin_cac') || ' months'))
  AND p.person_id NOT IN (SELECT person_id FROM candidato WHERE regla IN ('S1b', 'S1d') AND insuficiente IS NULL);
