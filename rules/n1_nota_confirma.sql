-- N1a enmendada (Ahmed, Sat 14 nov 2026): un CAC ALTERADO leído en una nota (≥30 mg/g o ≥3 mg/mmol, valor
-- y fecha leídos por el código en la cita comprobada) nunca retira el aviso.
-- S1c · Albuminuria persistente: si el paciente ya tiene S1b (CAC alterado de laboratorio, sin repetir y sin código
-- de ERC) y la nota es ≥3 meses posterior, la repetición ya está hecha y confirma la albuminuria: el pedido pasa
-- a «valorar código de ERC» (KDIGO 2024: cronicidad de al menos 3 meses). Sustituye a S1b. Nunca propone un fármaco.
-- Corre después del lector de notas y antes de la supresión. Sin notas, no hace nada.

CREATE TEMP VIEW nota_cac_alterado AS
SELECT h.rowid AS hid, h.*
FROM nota_hallazgo h
WHERE h.verificada = 1 AND h.etiqueta = 'ya_realizada' AND h.prueba = 'CAC'
  AND h.valor IS NOT NULL AND h.fecha_cita IS NOT NULL
  AND h.fecha_cita <= (SELECT hoy FROM ref)        -- vuelta 4 (Sol A2): defensa extra; verificar.py ya rechaza fechas futuras
  AND ((h.unidad = 'mg/g'    AND h.valor >= (SELECT valor FROM parametro WHERE clave = 'cac_umbral_mg_g'))
    OR (h.unidad = 'mg/mmol' AND h.valor >= (SELECT valor FROM parametro WHERE clave = 'cac_umbral_mg_mmol')));

CREATE TEMP TABLE s1c AS
SELECT c.person_id, u.valor AS valor_lab, u.unidad AS unidad_lab, u.fecha AS fecha_lab,
       n.valor AS valor_nota, n.unidad AS unidad_nota, n.fecha_cita, n.note_date, n.cita, n.note_id
FROM candidato c
JOIN cac_ultimo u ON u.person_id = c.person_id
JOIN nota_cac_alterado n ON n.person_id = c.person_id
WHERE c.regla = 'S1b' AND c.insuficiente IS NULL
  AND n.motivo_rechazo IS NULL                                   -- sin valor dudoso ni causa transitoria
  AND NOT EXISTS (SELECT 1 FROM nota_hallazgo z                   -- un CAC normal posterior anula la persistencia
                  WHERE z.person_id = c.person_id AND z.verificada = 1 AND z.prueba = 'CAC' AND z.valor IS NOT NULL
                    AND z.fecha_cita > n.fecha_cita
                    AND NOT EXISTS (SELECT 1 FROM nota_cac_alterado a WHERE a.hid = z.rowid))
  -- Vuelta 10 (Ahmed, 14 nov): el CAC citado en la nota solo cuenta si es de los últimos 12 meses (meses_nota_realizada).
  AND n.fecha_cita >= (SELECT date(hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_nota_realizada') || ' months') FROM ref)
  AND n.fecha_cita >= date(c.fecha_origen, '+' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_persistencia_cac') || ' months')
  -- Bucle 1 (14 nov): la nota elegida es la última ALTERADA Y LIMPIA (sin causa transitoria ni valor dudoso) que
  -- cumple los 3 meses. Una nota posterior con ITU o fiebre no borra una persistencia ya confirmada; un CAC
  -- normal posterior sí (arriba).
  AND n.hid = (SELECT n2.hid FROM nota_cac_alterado n2 WHERE n2.person_id = c.person_id AND n2.motivo_rechazo IS NULL
                 AND n2.fecha_cita >= (SELECT date(hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_nota_realizada') || ' months') FROM ref)
                 AND n2.fecha_cita >= date(c.fecha_origen, '+' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_persistencia_cac') || ' months')
                 ORDER BY n2.fecha_cita DESC, n2.note_id LIMIT 1);

INSERT INTO candidato (person_id, regla, grupo, prioridad, prueba, motivo, pedido, nota, fecha_origen, insuficiente)
SELECT s.person_id, 'S1c', 2, 2, 'ERC',
       'CAC ' || printf('%g', s.valor_lab) || ' ' || s.unidad_lab || ' (laboratorio, ' || s.fecha_lab || ') → ' ||
         printf('%g', s.valor_nota) || ' ' || s.unidad_nota || ' (informe externo en nota, pendiente de validar/incorporar; nota del ' || s.note_date || ', cita comprobada: «' || s.cita || '»)',
       'Albuminuria persistente: valorar código de ERC (N18)',
       'Posible albuminuria persistente en dos determinaciones separadas ≥3 meses (lab + informe externo en nota, pendiente de validar/incorporar; KDIGO 2024): valorar diagnóstico de ERC.',
       s.fecha_cita,
       NULL
FROM s1c s;

-- La repetición que pedía S1b ya está hecha (en la nota): S1c la sustituye.
DELETE FROM candidato WHERE regla = 'S1b' AND person_id IN (SELECT person_id FROM s1c);
