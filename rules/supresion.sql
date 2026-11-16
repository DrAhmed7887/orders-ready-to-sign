-- Supresión: decide quién sale en la lista y quién va al registro «Fuera de la lista, y por qué».
-- 1. Extracto incompleto → todo «información insuficiente».
-- 2. Fila marcada insuficiente por la regla.
-- 3. Pedido pendiente y vigente (≤3 meses, D1 firmada 14 nov 2026) de TODAS las pruebas del pedido.
--    Si el pedido tiene dos pruebas (S3: FGe + CAC) y solo una está pendiente, el aviso sigue
--    y el pedido preparado pide solo la que falta.
-- 4. Prueba ya realizada según una nota (N1a, firmada 14 nov 2026): solo filas de nota_hallazgo con la cita
--    comprobada por el código, la misma prueba, una fecha leída en la cita POSTERIOR al dato que dispara el aviso
--    y de los últimos 12 meses. Se comporta como un pedido pendiente: cubre solo esa prueba.
--    Rechazo (N1b) y Nefrología (N1c) nunca sacan a nadie: solo anotan (ejecutar.py).
-- 1b. Vuelta 13 (R2): diálisis, trasplante renal, paliativos o embarazo reciente → «Excluido: …», nunca a la lista.
-- 4b. Vuelta 13 (R5): una nota solo retira un CAC; un FGe en una nota añade una línea gris, nunca retira.
-- El primer motivo que se cumple es el que se registra.

CREATE TEMP VIEW pendiente_vigente AS
SELECT p.person_id, p.prueba, MAX(p.fecha_pedido) AS fecha_pedido
FROM pedido_pendiente p CROSS JOIN ref
WHERE p.fecha_pedido <= ref.hoy
  AND p.fecha_pedido >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_pedido_vigente') || ' months')
GROUP BY p.person_id, p.prueba;

CREATE TEMP VIEW nota_cubre AS
SELECT h.person_id, h.prueba, h.fecha_cita, h.cita, h.note_id, h.note_date
FROM nota_hallazgo h CROSS JOIN ref
WHERE h.verificada = 1 AND h.etiqueta = 'ya_realizada' AND h.fecha_cita IS NOT NULL
  AND h.prueba = 'CAC'      -- vuelta 13 (Ahmed, 16 nov 2026), R5: una nota nunca retira un pedido de FGe; solo anota
  AND h.fecha_cita <= ref.hoy
  AND NOT EXISTS (SELECT 1 FROM nota_cac_alterado a WHERE a.hid = h.rowid)   -- N1a enmendada: un CAC alterado nunca retira
  AND h.fecha_cita >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_nota_realizada') || ' months');

-- Para cada prueba del candidato, qué la cubre ya: un pedido vigente o, si no, una nota (la más reciente).
CREATE TEMP VIEW cobertura AS
SELECT c.*,
       p1.fecha_pedido AS pedido1, p2.fecha_pedido AS pedido2,
       (SELECT n.note_id FROM nota_cubre n WHERE n.person_id = c.person_id AND n.prueba = c.prueba
          AND (c.fecha_origen IS NULL OR n.fecha_cita > c.fecha_origen) ORDER BY n.fecha_cita DESC, n.note_id LIMIT 1) AS nota1,
       (SELECT n.note_id FROM nota_cubre n WHERE n.person_id = c.person_id AND n.prueba = c.prueba_extra
          AND (c.fecha_origen IS NULL OR n.fecha_cita > c.fecha_origen) ORDER BY n.fecha_cita DESC, n.note_id LIMIT 1) AS nota2
FROM candidato c
LEFT JOIN pendiente_vigente p1 ON p1.person_id = c.person_id AND p1.prueba = c.prueba
LEFT JOIN pendiente_vigente p2 ON p2.person_id = c.person_id AND p2.prueba = c.prueba_extra;

CREATE TEMP VIEW cobertura_texto AS
SELECT c.*,
       CASE WHEN c.pedido1 IS NOT NULL THEN 'ya solicitado el ' || c.pedido1
            WHEN c.nota1 IS NOT NULL THEN (SELECT 'ya realizado según nota del ' || n.note_date || ': «' || n.cita || '»'
                                           FROM nota_cubre n WHERE n.note_id = c.nota1 AND n.prueba = c.prueba LIMIT 1)
       END AS d1,
       CASE WHEN c.pedido2 IS NOT NULL THEN 'ya solicitado el ' || c.pedido2
            WHEN c.nota2 IS NOT NULL THEN (SELECT 'ya realizado según nota del ' || n.note_date || ': «' || n.cita || '»'
                                           FROM nota_cubre n WHERE n.note_id = c.nota2 AND n.prueba = c.prueba_extra LIMIT 1)
       END AS d2
FROM cobertura c;

CREATE TEMP VIEW candidato_motivo AS
SELECT c.person_id, c.regla, c.grupo, c.prioridad, c.prueba, c.prueba_extra, c.motivo,
       c.fecha_origen, c.insuficiente,
       CASE WHEN c.pedido1 IS NULL THEN c.nota1 END AS nota_usada1,
       CASE WHEN c.pedido2 IS NULL THEN c.nota2 END AS nota_usada2,
       -- La línea de nota dice lo mismo que el pedido: si una prueba ya está pedida, solo se solicita la otra.
       CASE
         WHEN c.prueba_extra IS NOT NULL AND c.d1 IS NOT NULL AND c.d2 IS NULL
           THEN substr(c.nota, 1, instr(c.nota, ':')) || ' se solicita ' || c.prueba_extra ||
                ' (' || c.prueba || ' ' || c.d1 || ').'
         WHEN c.prueba_extra IS NOT NULL AND c.d1 IS NULL AND c.d2 IS NOT NULL
           THEN substr(c.nota, 1, instr(c.nota, ':')) || ' se solicita ' || c.prueba ||
                ' (' || c.prueba_extra || ' ' || c.d2 || ').'
         ELSE c.nota
       END AS nota,
       CASE
         WHEN c.prueba_extra IS NOT NULL AND c.d1 IS NOT NULL AND c.d2 IS NULL
           THEN substr(c.pedido, 1, instr(c.pedido, ':')) || ' solicitar ' || c.prueba_extra ||
                ', valorar (' || c.prueba || ' ' || c.d1 || ')'
         WHEN c.prueba_extra IS NOT NULL AND c.d1 IS NULL AND c.d2 IS NOT NULL
           THEN substr(c.pedido, 1, instr(c.pedido, ':')) || ' repetir ' || c.prueba ||
                ', valorar (' || c.prueba_extra || ' ' || c.d2 || ')'
         ELSE c.pedido
       END AS pedido,
       CASE
         WHEN (SELECT extracto_completo FROM ref) = 0
           THEN 'Información insuficiente: el extracto está incompleto'
         WHEN c.person_id IN (SELECT person_id FROM excluido_motivo)
           THEN 'Excluido: ' || (SELECT motivo FROM excluido_motivo e WHERE e.person_id = c.person_id)
         WHEN c.insuficiente IS NOT NULL
           THEN c.insuficiente
         WHEN c.pedido1 IS NOT NULL AND (c.prueba_extra IS NULL OR c.pedido2 IS NOT NULL)
           THEN 'Pedido ya pendiente: ' || c.prueba || ' solicitado el ' || c.pedido1 ||
                CASE WHEN c.prueba_extra IS NOT NULL
                     THEN ' y ' || c.prueba_extra || ' el ' || c.pedido2 ELSE '' END
         WHEN c.d1 IS NOT NULL AND (c.prueba_extra IS NULL OR c.d2 IS NOT NULL)
           THEN 'Ya cubierto: ' || c.prueba || ' ' || c.d1 ||
                CASE WHEN c.prueba_extra IS NOT NULL
                     THEN ' y ' || c.prueba_extra || ' ' || c.d2 ELSE '' END
       END AS motivo_supresion
FROM cobertura_texto c;

CREATE TEMP VIEW en_lista AS
SELECT * FROM candidato_motivo WHERE motivo_supresion IS NULL;

CREATE TEMP VIEW fuera_de_la_lista AS
SELECT * FROM candidato_motivo WHERE motivo_supresion IS NOT NULL;
