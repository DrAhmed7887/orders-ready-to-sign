// English mode for the doctor's screen (ui/index.html?lang=en).
// The screen and the rules stay in Spanish (they are built for Spanish primary care); this layer translates what is
// shown, in the browser, after each render. It never changes data or decisions.
// Not translated on purpose: text inside «…» (quoted from a clinical note) and elements marked lang="es"
// (the original free-text notes). Patient names, codes (ICD-10, ATC, LOINC) and numbers are kept.
// Checked by ui/tests/idioma.test.mjs: in English mode no Spanish words remain outside those two places.
(function () {
  "use strict";
  const params = new URLSearchParams(location.search);
  const EN = params.get("lang") === "en";

  // ---- language switch in the header (both modes) -------------------------------------------------------
  function addSwitch() {
    const h = document.querySelector("header");
    if (!h || h.querySelector(".btn-idioma")) return;
    const destino = () => {   // built from the current address at click time (the cohort may have changed)
      const p = new URLSearchParams(location.search);
      if (EN) p.delete("lang"); else p.set("lang", "en");
      return location.pathname + (p.toString() ? "?" + p : "") + location.hash;
    };
    const a = document.createElement("a");
    a.className = "btn-idioma";
    a.href = destino();
    a.textContent = EN ? "Español" : "English";
    a.setAttribute("lang", EN ? "es" : "en");
    a.style.cssText = "margin-left:8px;font-size:13px;font-weight:700;padding:4px 10px;border:1px solid var(--borde);border-radius:999px;text-decoration:none";
    a.addEventListener("click", () => { a.href = destino(); });
    h.appendChild(a);
  }
  if (!EN) { document.addEventListener("DOMContentLoaded", addSwitch); if (document.readyState !== "loading") addSwitch(); return; }

  document.documentElement.lang = "en";

  // ---- whole strings (after trimming) --------------------------------------------------------------------
  const EXACT = new Map(Object.entries({
    "Estación Clínica AP · Pedidos para firmar": "Primary-care station · Orders to sign",
    "Historia de salud · Atención Primaria": "Health record · Primary care",
    "— entorno de demostración": "— demo environment",
    "MAQUETA · no es un sistema oficial · datos sintéticos": "MOCK-UP · not an official system · synthetic data",
    "Módulo de cribado renal integrado en el puesto (maqueta)": "Kidney screening module inside the doctor's workstation (mock-up)",
    "Sin conexión · datos sintéticos · trazable": "Offline · synthetic data · traceable",
    "Dra. Carmen López": "Dr Carmen López",
    "Agenda de hoy": "Today's clinic",
    "Pedidos para firmar": "Orders to sign",
    "Consulta AP · Historia": "Clinic · Health record",
    "Fuera de la lista": "Left off the list",
    "Desconocido ≠ Normal": "Unknown ≠ Normal",
    "Registro de decisiones": "Decision log",
    "Página local, sin conexión · trazable.": "Local page, offline · traceable.",
    "Nunca propone un fármaco; el diagnóstico lo decide el médico. Cada pedido espera tu firma.": "It never proposes a drug; the diagnosis is the doctor's. Every order waits for your signature.",
    "pedidos renales que un filtro básico no ve": "kidney orders a basic filter does not see",
    ". La orden y la línea de nota ya están escritas: solo falta tu firma.": ". The order and the note line are already written: only your signature is missing.",
    "para firmar un pedido desde la lista": "to sign an order from the list",
    "fuera de la lista, cada uno con su motivo": "left off the list, each with its reason",
    "Cupo crónico": "Chronic patient list",
    "Reglas": "Rules",
    "Supresión": "Suppression",
    "pedido pendiente o datos insuficientes": "order already pending or not enough data",
    "Preparado": "Prepared",
    "orden + línea de nota": "order + note line",
    "Tú decides": "You decide",
    "firmar · aplazar · descartar": "sign · postpone · dismiss",
    "Abrir ficha": "Open record",
    "Empeorando": "Getting worse",
    "función renal en descenso": "kidney function falling",
    "Hipertensión": "Hypertension",
    "Pedido": "Order",
    "Revisión": "Review",
    "Firmar": "Sign",
    "Descartar…": "Dismiss…",
    "Sin seguimiento": "No follow-up",
    "albuminuria sin confirmar": "albuminuria not confirmed",
    "Prueba pendiente": "Test due",
    "cribado anual vencido": "annual screening overdue",
    "Ver por qué": "See why",
    "Medido en esta sesión:": "Measured in this session:",
    "clics": "clicks",
    "clic": "click",
    "1 clic": "1 click",
    "firmados": "signed",
    "aplazados o descartados": "postponed or dismissed",
    "pendientes": "pending",
    "Descartar:": "Dismiss:",
    "El motivo queda en el registro. No se vuelve a proponer con los mismos datos.": "The reason is logged. It is not proposed again with the same data.",
    "Cancelar": "Cancel",
    "Descartar": "Dismiss",
    "Cohorte de demostración": "Demo cohort",
    "Secciones": "Sections",
    "Resultado de la revisión": "Result of the review",
    "Cómo se ha preparado esta lista": "How this list was prepared",
    "Pacientes citados hoy que tienen un pedido preparado": "Patients booked today who have an order ready",
    "Hora": "Time",
    "Paciente": "Patient",
    "Pedido preparado": "Order ready",
    "Estado": "Status",
    "Consulta AP": "Clinic",
    "pendiente": "pending",
    "Fuera de la lista, y por qué": "Left off the list, and why",
    "No molesta cuando no debe: cada paciente que la revisión deja fuera queda aquí con su motivo.": "It stays quiet when it should: every patient the review leaves out is listed here with the reason.",
    "Pedidos ya en curso (sin duplicados ni fatiga)": "Orders already in progress (no duplicates, no alert fatigue)",
    "Pruebas ya solicitadas o confirmadas con cita literal en nota clínica.": "Tests already ordered, or confirmed by a verbatim quote in a clinical note.",
    "Regla": "Rule",
    "Hallazgo": "Finding",
    "Por qué no está en la lista": "Why it is not on the list",
    "Desconocido ≠ Normal · Información insuficiente": "Unknown ≠ Normal · Not enough information",
    "Casos excluidos por falta de datos, unidad no clasificable o extracto incompleto (nunca asumidos como normales).": "Cases left out for missing data, an unknown unit or an incomplete extract (never assumed to be normal).",
    "Comparación con un filtro básico": "Comparison with a basic filter",
    "pacientes, de los que": "patients, of whom",
    "están entre los": "are among the",
    "Pedidos ya en curso": "Orders already in progress",
    "Información insuficiente": "Not enough information",
    "Cada firma, aplazamiento o descarte, con su hora y su motivo": "Every signature, postponement or dismissal, with its time and reason",
    "Decisión": "Decision",
    "Motivo": "Reason",
    "Aún no hay decisiones.": "No decisions yet.",
    "Exportar registro (JSON)": "Export log (JSON)",
    "Citados hoy": "Booked today",
    "Paciente sintético": "Synthetic patient",
    "NHC": "Record no.",
    "SIP": "Health card",
    "Cita": "Appointment",
    "Alergias / Alertas": "Allergies / Alerts",
    "no constan en el extracto": "none in the extract",
    "Problemas de salud": "Health problems",
    "Diabetes mellitus tipo 2": "Type 2 diabetes mellitus",
    "Enfermedad renal crónica": "Chronic kidney disease",
    "no codificada: la valora el médico": "not coded: for the doctor to assess",
    "Episodio actual": "Current episode",
    "Control de crónicos · consulta de hoy": "Chronic-care check · today's visit",
    "Control de crónicos · revisión de cupo": "Chronic-care check · list review",
    "Hoja de evolución": "Progress notes",
    "Resultados": "Results",
    "Prescripción": "Prescriptions",
    "Peticiones en curso": "Orders in progress",
    "Peticiones en curso:": "Orders in progress:",
    "Petición clínica · módulo de cribado renal": "Clinical request · kidney screening module",
    "Solicitar laboratorio": "Lab request",
    "Especialidad": "Specialty",
    "Medicina familiar": "Family medicine",
    "Prioridad": "Priority",
    "Ordinaria": "Routine",
    "Preparada · falta tu firma": "Ready · waiting for your signature",
    "Orden / acción preparada": "Prepared order / action",
    "Motivo de solicitud (por qué aparece)": "Reason for the request (why it appears)",
    "De dónde sale (tablas del extracto)": "Where it comes from (extract tables)",
    "sin dispensaciones registradas": "no dispensing recorded",
    "ningún pedido vigente": "no current order",
    "ninguna nota con una cita comprobada": "no note with a checked quote",
    "Línea para el evolutivo": "Line for the progress note",
    "Aplazar": "Postpone",
    "Estación clínica de atención primaria (maqueta)": "Primary-care workstation (mock-up)",
    "Pacientes citados": "Booked patients",
    "Cabecera del paciente": "Patient header",
    "Hallazgo del módulo": "Module finding",
    "Historia de salud": "Health record",
    "Módulo de cribado renal": "Kidney screening module",
    "← Pedidos para firmar": "← Orders to sign",
    "Abrir en Consulta AP · Historia →": "Open in Clinic · Health record →",
    "Por qué aparece": "Why it appears",
    "Decisión de diseño: solo FGe de los últimos 36 meses entran en la tendencia": "Design decision: only eGFR values from the last 36 months enter the trend",
    "Sin un pedido pendiente que ya lo cubra": "No pending order already covers it",
    "Decisión de diseño: un pedido de más de 3 meses sin resultado ya no suprime": "Design decision: an order older than 3 months with no result no longer suppresses",
    "Resultados renales (procedencia)": "Kidney results (provenance)",
    "Cada valor sale del extracto, con su fecha": "Every value comes from the extract, with its date",
    "Fecha": "Date",
    "Prueba": "Test",
    "Resultado": "Result",
    "CAC (orina)": "ACR (urine)",
    "De dónde sale": "Where it comes from",
    "Orden de laboratorio": "Lab order",
    "Orden": "Order",
    "Línea de nota": "Note line",
    "La decisión queda registrada con su hora, solo en este navegador. Nunca propone un fármaco; el diagnóstico lo decide el médico.": "The decision is logged with its time, in this browser only. It never proposes a drug; the diagnosis is the doctor's.",
    "Resultados renales": "Kidney results",
    "Revisión de cupo": "List review",
    "Hipertensión arterial esencial": "Essential hypertension",
    "Determinación": "Test",
    "Cociente albúmina/creatinina (orina)": "Albumin-to-creatinine ratio (urine)",
    "Filtrado glomerular estimado": "Estimated glomerular filtration rate",
    "Dispensaciones (": "Dispensing (",
    "Una prueba ya pedida no se vuelve a pedir: el módulo la deja fuera de la lista.": "A test already ordered is not ordered again: the module leaves it off the list.",
    "Hoy en consulta": "In clinic today",
    "Sin repetir en más de 6 meses": "Not repeated in more than 6 months",
    "Decisión de diseño (la guía no da cifra)": "Design decision (the guideline gives no number)",
    "población del cupo crónico": "chronic patient list",
    "Diabetes tipo 2, hipertensión o FGe <60": "Type 2 diabetes, hypertension or eGFR <60",
    "Sin CAC en los últimos 12 meses": "No ACR in the last 12 months",
    "PROT-AP ERC 2025: cribado anual con FGe y CAC": "PROT-AP ERC 2025 (Valencian protocol): annual screening with eGFR and ACR",
    "Ya valorado en otra consulta": "Already assessed in another visit",
    "Seguimiento en nefrología u otro centro": "Followed by nephrology or another centre",
    "El paciente no lo desea": "The patient does not want it",
    "Dato erróneo en la historia": "Wrong data in the record",
    "Otro": "Other",
    "firmado": "signed",
    "aplazado": "postponed",
    "descartado": "dismissed",
    "Firmado": "Signed",
    "Aplazado": "Postponed",
    "Descartado": "Dismissed",
    "deshacer": "undo",
    "pedidos preparados para firmar": "orders ready to sign",
    "Ver en Consulta AP": "See in Clinic",
    "Señal reconstruida cruzando": "Signal rebuilt by crossing",
    "(ninguno vigente) +": "(none current) +",
    "informe externo en nota (pendiente de validar/incorporar)": "external report in a note (to be validated/entered)",
    "Ver la agenda de hoy": "See today's clinic",
    "ERC codificada": "CKD coded",
    "Albuminuria persistente: valorar código de ERC (N18)": "Persistent albuminuria: consider a CKD code (N18)",
    "Sin ningún CAC registrado": "No ACR ever recorded",
    "Hoy": "Today",
    "Resumen cohorte Aguja": "Needle cohort summary",
    "el paciente sigue en la lista por otro hallazgo": "the patient stays on the list for another finding",
    "· Medicina de familia · Evolutivo (texto libre)": "· Family medicine · Progress note (free text)",
    "✓ Frase comprobada por el código: está literalmente en la nota, nombra la prueba, y la fecha y el valor los leyó el código, no el modelo.": "✓ Sentence checked by the code: it is word for word in the note, it names the test, and the date and value were read by the code, not the model.",
    "Valoración clínica (KDIGO / N18)": "Clinical assessment (KDIGO / N18)",
    "Elegir otro paciente de la cohorte": "Choose another patient in the cohort",
    "Frase comprobada por el código": "Sentence checked by the code",
    "Nota clínica (cita comprobada)": "Clinical note (checked quote)",
    "CAC ya incluido en el pedido principal": "ACR already in the main order",
    "Firmar, aplazar o descartar se aplica a todo lo anterior.": "Sign, postpone or dismiss applies to everything above.",
    "En la misma petición": "In the same request",
    "Una nota trae otro CAC ≥30 mg/g al menos 3 meses después, con la cita comprobada por el código": "A note brings another ACR ≥30 mg/g at least 3 months later, with the quote checked by the code",
    "El lector local solo lee la nota; el valor, la fecha y la regla los comprueba el código": "The local reader only reads the note; the code checks the value, the date and the rule",
    "Valoración clínica": "Clinical assessment",
    "pedido preparado": "order ready",
    "Hoy · presencial": "Today · in person",
    "Calibrado con IBERICAN, BDCAP 2016, Girona Sud y BIG-PAC · etiquetas independientes del SQL": "Calibrated with IBERICAN, BDCAP 2016, Girona Sud and BIG-PAC · labels independent of the SQL",
    "Sin evolutivos en los últimos 12 meses en el extracto.": "No progress notes in the last 12 months in the extract.",
    "Pedido no encontrado": "Order not found",
    "Volver a los pedidos": "Back to the orders",
    "ninguno": "none",
    "Revisar el último CAC": "Review the last ACR",
    "Revisar unidad del FGe": "Check the eGFR unit",
    "Solicitar CAC": "Order ACR",
    "Función renal en descenso: repetir FGe + CAC, valorar": "Kidney function falling: repeat eGFR + ACR, assess",
    "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana": "Albuminuria not confirmed: repeat ACR on a first-morning urine",
    "Albuminuria persistente en dos analíticas: valorar código de ERC (N18)": "Persistent albuminuria in two lab results: consider a CKD code (N18)",
    "Revisar el FGe": "Check the eGFR",
    "Diabetes tipo 1": "Type 1 diabetes",
    "Excluidos de la lista": "Excluded from the list",
    "Diálisis, trasplante renal, cuidados paliativos o embarazo reciente: estos pedidos no se proponen.": "Dialysis, kidney transplant, palliative care or recent pregnancy: these orders are not proposed.",
    "Ningún paciente excluido en este extracto.": "No patient excluded in this extract.",
    "Motivo": "Reason",
    "fuera: excluidos (diálisis, trasplante, paliativos, embarazo)": "left off: excluded (dialysis, transplant, palliative care, pregnancy)",
    "Cambio >20 %: repetir analítica": "Change >20 %: repeat the blood test",
    "Inicio de iSRA/iSGLT2 hace <3 meses: descenso esperable hasta 30 % (KDIGO 2024) — revisar": "RAS inhibitor/SGLT2 inhibitor started <3 months ago: a fall of up to 30 % is expected (KDIGO 2024) — review",
    "Agujas en el pajar (S1c):": "Needles in the haystack (S1c):",
    "No se muestra ningún pedido: todo lo que se pudo evaluar está en “Fuera de la lista” como información insuficiente.": "No order is shown: everything that could be assessed is in “Left off the list” as not enough information.",
    "Nunca propone un fármaco; el diagnóstico lo decide el médico. La decisión aparece también en “Pedidos para firmar” y en el “Registro de decisiones”.": "It never proposes a drug; the diagnosis is the doctor's. The decision also appears in “Orders to sign” and in the “Decision log”.",
    "Cardiopatía hipertensiva": "Hypertensive heart disease",
    "Enfermedad renal hipertensiva": "Hypertensive kidney disease",
    "Enfermedad cardiorrenal hipertensiva": "Hypertensive heart and kidney disease",
    "Hipertensión secundaria": "Secondary hypertension",
    "Hipertensión esencial": "Essential hypertension",
    "Caída aislada >20 % entre los dos últimos FGe": "Isolated fall >20 % between the last two eGFR values",
    "Motivo de revisión manual": "Reason for manual review",
    "Resumen del cupo AP español": "Summary of the Spanish primary-care list",
    "Sin diagnósticos codificados en el extracto": "No coded diagnoses in the extract",
    "Sin una tendencia que ya cumpla la regla S3": "No trend already meeting rule S3",
    "albuminuria persistente leída en nota: valorar N18 (S1c)": "persistent albuminuria read in a note: consider N18 (S1c)",
    "albuminuria sin repetir (S1b)": "albuminuria not repeated (S1b)",
    "cribado anual de CAC vencido (S1a)": "annual ACR screening overdue (S1a)",
    "con cita hoy: el pedido sale en la consulta": "booked today: the order shows up in the visit",
    "con un pedido retirado que siguen en la lista por otro": "with an order withdrawn who stay on the list for another finding",
    "fuera: Desconocido ≠ Normal": "left off: Unknown ≠ Normal",
    "fuera: ya pedido o ya hecho según nota": "left off: already ordered or already done according to a note",
  }));

  // ---- fixed phrases that also appear inside longer strings (substring, longest first) -------------------
  const PHRASES = [
    "Albuminuria persistente: valorar código de ERC (N18)", "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana",
    "Albuminuria persistente en dos analíticas: valorar código de ERC (N18)", "Revisar el FGe",
    "Cambio >20 %: repetir analítica", "Función renal en descenso: repetir FGe + CAC, valorar", "Revisar el último CAC",
    "Revisar unidad del FGe", "Solicitar CAC", "Sin ningún CAC registrado", "CAC ya incluido en el pedido principal",
    "Inicio de iSRA/iSGLT2 hace <3 meses: descenso esperable hasta 30 % (KDIGO 2024) — revisar",
  ].sort((a, b) => b.length - a.length).map(k => [k, EXACT.get(k)]);
  for (const [k, v] of PHRASES) if (!v) throw new Error("i18n: missing phrase " + k);

  // ---- phrases inside longer strings (applied in order, before the token pass) --------------------------
  const RULES = [
    [/sin repetir en (\d+) meses y sin código de ERC/g, "not repeated in $1 months and no CKD code"],
    [/\(laboratorio, ([^)]+)\)/g, "(lab, $1)"],
    [/\(informe externo en nota, pendiente de validar\/incorporar; nota del ([^,]+), cita comprobada: /g, "(external report in a note, to be validated/entered; note of $1, checked quote: "],
    [/informe externo en nota, pendiente de validar\/incorporar/g, "external report in a note, to be validated/entered"],
    [/Posible albuminuria persistente en dos determinaciones separadas ≥(\d+) meses/g, "Possible persistent albuminuria in two results ≥$1 months apart"],
    [/lab \+ external report/g, "lab + external report"],
    [/^Nota del (.+?) \(CAC, no retira el aviso: posible causa transitoria en la nota\): /, "Note of $1 (ACR, does not withdraw the alert: possible transient cause in the note): "],
    [/^Nota del (.+?) \(CAC, no retira el aviso: resultado alterado en la nota\): /, "Note of $1 (ACR, does not withdraw the alert: abnormal result in the note): "],
    [/^Nota del (.+?) \(FGe, no retira el aviso: una nota no retira un pedido de FGe\): /, "Note of $1 (eGFR, does not withdraw the alert: a note never withdraws an eGFR order): "],
    [/^Nota del (.+?) \(CAC, no retira el aviso: sin fecha en la cita\): /, "Note of $1 (ACR, does not withdraw the alert: no date in the quote): "],
    [/^Nota del (.+?) \(CAC, no retira el aviso: valor del CAC dudoso \(sin valor legible ni «\d+», sin unidad o con varios resultados\)\): /, "Note of $1 (ACR, does not withdraw the alert: unclear ACR value (no readable value or «normal», no unit, or several results)): "],
    [/^Rechazó la prueba \(nota del (.+?)\): /, "Declined the test (note of $1): "],
    [/^Seguido en Nefrología \(nota del (.+?)\): /, "Followed by nephrology (note of $1): "],
    [/: valorar diagnóstico de (\w+)\./g, ": consider a $1 diagnosis."],
    [/\bsin diagnósticos\b/g, "no diagnoses"],
    [/\by (\d+) más\b/g, "and $1 more"],
    [/el filtro básico \(último (\w+) <(\d+)\)/g, "the basic filter (last $1 <$2)"],
    [/(\w+) ya incluido en el pedido principal/g, "$1 already in the main order"],
    [/Sin ningún (\w+) registrado/g, "No $1 ever recorded"],
    [/Último (\w+) el (.+?) \((\d+) meses\)/g, "Last $1 on $2 ($3 months)"],
    [/^Hoy (\d+:\d+)$/, "Today $1"],
    [/^Paciente (\d+)/, "Patient $1"],
    [/Información insuficiente: el último CAC no tiene resultado numérico/g, "Not enough information: the last ACR has no numeric result"],
    [/Información insuficiente: unidad del CAC desconocida/g, "Not enough information: unknown ACR unit"],
    [/Información insuficiente: unidad del FGe no reconocida/g, "Not enough information: eGFR unit not recognised"],
    [/unidad del FGe no reconocida/g, "eGFR unit not recognised"],
    [/Pedido ya pendiente: (\w+) solicitado el /g, "Order already pending: $1 ordered on "],
    [/Ya cubierto: (\w+) ya realizado según nota del (.+?): /g, "Already covered: $1 already done according to the note of $2: "],
    [/(\w+) ya realizado según nota del (.+?): /g, "$1 already done according to the note of $2: "],
    [/Función renal en descenso: repetir FGe, valorar \(CAC ya solicitado el ([^)]+)\)/g, "Kidney function falling: repeat eGFR, assess (ACR already ordered on $1)"],
    [/Función renal en descenso: solicitar CAC, valorar \(FGe ya solicitado el ([^)]+)\)/g, "Kidney function falling: order ACR, assess (eGFR already ordered on $1)"],
    [/Función renal en descenso: solicitar CAC, valorar \(/g, "Kidney function falling: order ACR, assess ("],
    [/Descenso de FGe \(KDIGO (\d+), rec\. ([\d.]+)\): se solicita FGe y CAC\./g, "Falling eGFR (KDIGO $1, rec. $2): eGFR and ACR ordered."],
    [/Descenso de FGe \(KDIGO (\d+), rec\. ([\d.]+)\): se solicita (\w+) \((\w+) ya solicitado el ([^)]+)\)\./g, "Falling eGFR (KDIGO $1, rec. $2): $3 ordered ($4 already ordered on $5)."],
    [/Descenso de FGe \(KDIGO (\d+), rec\. ([\d.]+)\): se solicita (\w+) \(/g, "Falling eGFR (KDIGO $1, rec. $2): $3 ordered ("],
    [/CAC alterado sin confirmar \(KDIGO (\d+), PP ([\d.]+) y ([\d.]+)\): se solicita repetición en primera orina de la mañana \(chorro medio\); evitar durante la menstruación, tras ejercicio intenso o con infección urinaria sintomática o hematuria \(tabla 16\)\./g, "Abnormal ACR not confirmed (KDIGO $1, PP $2 and $3): repeat ordered on a first-morning midstream urine; avoid during menstruation, after hard exercise, or with a symptomatic urine infection or blood in the urine (Table 16)."],
    [/Albuminuria en dos determinaciones de laboratorio separadas ≥3 meses \(KDIGO (\d+), PP ([\d.]+)\): valorar diagnóstico de ERC\./g, "Albuminuria in two lab results ≥3 months apart (KDIGO $1, PP $2): consider a CKD diagnosis."],
    [/, sin CAC normal entre medias y sin código de ERC/g, ", no normal ACR in between and no CKD code"],
    [/Excluido: diálisis/g, "Excluded: dialysis"], [/Excluido: trasplante renal/g, "Excluded: kidney transplant"],
    [/Excluido: cuidados paliativos/g, "Excluded: palliative care"], [/Excluido: embarazo o puerperio reciente/g, "Excluded: recent pregnancy or postpartum"],
    [/Información insuficiente: CAC con valor imposible/g, "Not enough information: impossible ACR value"],
    [/Información insuficiente: FGe con valor imposible/g, "Not enough information: impossible eGFR value"],
    [/Información insuficiente: FGe de distintas ecuaciones \(MDRD, CKD-EPI\); no se calcula la tendencia/g, "Not enough information: eGFR from different equations (MDRD, CKD-EPI); no trend computed"],
    [/FGe de distintas ecuaciones en los últimos 36 meses/g, "eGFR from different equations in the last 36 months"],
    [/FGe con valor imposible/g, "eGFR with an impossible value"],
    [/Caída de FGe >(\d+) % \(KDIGO (\d+), PP ([\d.]+)\): se repite la analítica\./g, "eGFR fall >$1 % (KDIGO $2, PP $3): blood test repeated."],
    [/Cribado anual de ERC \(PROT-AP ERC (\d+)\): se solicita CAC\./g, "Annual CKD screening (PROT-AP ERC $1): ACR ordered."],
    [/: cambio de (-?[\d,.]+) %/g, ": change of $1 %"],
    [/paso de (G\w+) → (G\w+) con caída de ([\d,.]+) %/g, "moved from $1 → $2 with a fall of $3 %"],
    [/\((.+?) a (.+?), (\d+) valores\)/g, "($1 to $2, $3 values)"],
    [/ml\/min\/1,73 m²\/año/g, "ml/min/1.73 m²/year"],
    [/^Último CAC hace (\d+) meses; el cribado es cada (\d+) meses$/, "Last ACR $1 months ago; screening is every $2 months"],
    [/^Sin ningún CAC; el cribado es cada (\d+) meses$/, "No ACR at all; screening is every $1 months"],
    [/^Último CAC el (.+?) \((\d+) meses\)$/, "Last ACR on $1 ($2 months)"],
    [/^CAC sin resultado el /, "ACR with no result on "],
    [/^(\w+) con unidad /, "$1 with unit "],
    [/^También \((\d+)\): /, "Also ($1): "],
    [/^También en este pedido · /, "Also in this order · "],
    [/^Hoy en consulta · /, "In clinic today · "],
    [/^Hoy (\d+:\d+) · presencial$/, "Today $1 · in person"],
    [/^(\d+:\d+) · pedido preparado$/, "$1 · order ready"],
    [/^\(hoy (\d+:\d+)\) ·$/, "(today $1) ·"],
    [/^Y (\d+) más con cita hoy$/, "And $1 more booked today"],
    [/^(\d+) años · Mujer$/, "$1 years · Woman"],
    [/^(\d+) años · Hombre$/, "$1 years · Man"],
    [/^Ficha de (.+)$/, "$1's record"],
    [/^Caso Carmen · ([\d.,]+) pac\.$/, "Carmen's list · $1 pts"],
    [/^Aguja · (.+?) \(([\d.,]+) pac\.\)$/, "Needle · $1 ($2 pts)"],
    [/^Cupo AP Español · ([\d.,]+) pac\.$/, "Spanish primary-care list · $1 pts"],
    [/^Cupo AP Español · ([\d.,]+) adultos sintéticos$/, "Spanish primary-care list · $1 synthetic adults"],
    [/Cohorte Aguja \(([\d.,]+) pac\.\)/g, "Needle cohort ($1 pts)"],
    [/Cupo AP Español \(([\d.,]+) pac\.\)/g, "Spanish primary-care list ($1 pts)"],
    [/^Centro de salud \(ficticio\) · Consulta (\d+)$/, "Health centre (fictional) · Room $1"],
    [/^Consulta (\d+) ·$/, "Room $1 ·"],
    [/^Estación Clínica AP · Cupo Dra\. Carmen López$/, "Primary-care station · Dr Carmen López's list"],
    [/^Pedidos preparados para firmar · extracto del (.+)$/, "Orders ready to sign · extract of $1"],
    [/^Un filtro básico \(último FGe <(\d+)\) ve$/, "A basic filter (last eGFR <$1) sees"],
    [/^vistos por /, "seen by "],
    [/^(\d+) de (\d+) decididos$/, "$1 of $2 decided"],
    [/^(\d+) de (\d+)$/, "$1 of $2"],
    [/^([\d.,]+) pacientes$/, "$1 patients"],
    [/^([\d.,]+) fuera$/, "$1 left off"],
    [/^([\d.,]+) pedidos$/, "$1 orders"],
    [/^Fuera de la lista \((\d+)\)$/, "Left off the list ($1)"],
    [/^DM2, HTA o FGe <(\d+) · extracto completo$/, "T2D, hypertension or eGFR <$1 · complete extract"],
    [/^Regla (S\w+) · /, "Rule $1 · "],
    [/^Regla (S\w+)$/, "Rule $1"],
    [/ · la lista solo incluye pacientes que cumplen todas las condiciones/g, " · the list only includes patients who meet every condition"],
    [/lab \+ informe externo en nota, pendiente de validar\/incorporar/g, "lab + external report in a note, to be validated/entered"],
    [/^≥(\d+) FGe de los últimos (\d+) meses que abarcan ≥(\d+) meses$/, "≥$1 eGFR values from the last $2 months spanning ≥$3 months"],
    [/^Pendiente < -(\d+) ml\/min\/1[.,]73 m²\/(?:año|year), o bajada de categoría con caída ≥(\d+) %$/, "Slope < -$1 ml/min/1.73 m²/year, or a fall in category with a drop ≥$2 %"],
    [/^La señal está repartida entre (\d+) tablas del mismo extracto: las reglas las cruzan y el lector de notas aporta la frase$/, "The signal is split across $1 tables of the same extract: the rules cross them and the note reader brings the sentence"],
    [/^≥(\d+): sin alerta del filtro básico$/, "≥$1: no alert from the basic filter"],
    [/^Sin código de ERC \(N18\) en la historia$/, "No CKD code (N18) in the record"],
    [/^CAC ≥(\d+) mg\/g \(≥(\d+) mg\/mmol\)$/, "ACR ≥$1 mg/g (≥$2 mg/mmol)"],
    [/^CAC ≥(\d+) mg\/g en el laboratorio, sin repetir y sin código de ERC \((S\w+)\)$/, "ACR ≥$1 mg/g in the lab, not repeated and no CKD code ($2)"],
    [/^CAC en categoría (A\d)$/, "ACR in category $1"],
    [/^KDIGO (\d+), tabla (\d+): /, "KDIGO $1, table $2: "],
    [/ · KDIGO (\d+), tabla (\d+): /g, " · KDIGO $1, table $2: "],
    [/^Cribado renal: (\d+) pedidos? para firmar$/, "Kidney screening: $1 order(s) to sign"],
    [/^ERC sin codificar \(N18\)$/, "CKD not coded (N18)"],
    [/ · sin N18 \(ERC sin codificar\)/g, " · no N18 (CKD not coded)"],
    [/^(\w+) pedido el /, "$1 ordered on "],
    [/^Filtro de (\d+) variable \(último FGe <(\d+)\):$/, "$1-variable filter (last eGFR <$2):"],
    [/^pedidos de hoy\. Los hallazgos de la revisión se esconden detrás de valores “aceptables”\.$/, "of today's orders. The review's findings hide behind “acceptable” values."],
    [/^Desconocido ≠ Normal: un dato faltante, unidad desconocida o extracto incompleto nunca se rellena como normal por defecto; queda registrado para revis.*$/, "Unknown ≠ Normal: a missing value, unknown unit or incomplete extract is never filled in as normal by default; it is logged for review."],
    [/^En este extracto completo no hay casos bloqueados por información insuficiente.*$/, "In this complete extract no case is blocked by missing information; with any missing variable or an incomplete extract they would appear here for review."],
    [/^(.+?) (\d+) · Desconocido ≠ Normal \(estado clínico de primera clase\)$/, "$1 $2 · Unknown ≠ Normal (a first-class clinical state)"],
    [/^(.+?) (\d+) · Caza pacientes invisibles en (\d+) tablas OMOP$/, "$1 $2 · Finds invisible patients across $3 OMOP tables"],
    [/^Aguja en el pajar \(cohorte sintética · ([\d.,]+) pacientes\): (\d+) pedidos en el cupo · (\d+) único caso (S\w+) confirmado en nota \((.+?), pac\. (\d+)\)$/, "Needle in a haystack (synthetic cohort · $1 patients): $2 orders in the list · $3 single $4 case confirmed in a note ($5, pt $6)"],
    [/^\(DM2 (E11(?:\.\d)?), HTA (I10), sin N18\) \+$/, "(T2D $1, hypertension $2, no N18) +"],
    [/^\(CAC (\d+) mg\/g hace (\d+) meses, FGe (\d+) “normal”\) \+$/, "(ACR $1 mg/g $2 months ago, eGFR $3 “normal”) +"],
    [/^cupo crónico revisado \(DM2, HTA o FGe <(\d+)\) de /, "chronic list reviewed (T2D, hypertension or eGFR <$1) out of "],
    [/^función renal en descenso o caída \((.+)\)$/, "kidney function falling or dropping ($1)"],
    [/^N1a enmendada \(Ahmed, (.+?)\): dos CAC alterados separados ≥(\d+) meses = persistente \(KDIGO (\d+), cronicidad de al menos (\d+) meses\)$/, "N1a as amended (Ahmed, $1): two abnormal ACRs ≥$2 months apart = persistent (KDIGO $3, chronicity of at least $4 months)"],
    [/^notas\/verificar\.py · regla N1 \(firmada (.+)\)$/, "notas/verificar.py · rule N1 (signed $1)"],
    [/, y por qué/g, ", and why"],
    [/hace (<?\d+) (meses|años|días)/g, "$1 $2 ago"],   // last: the specific rules above match "hace" first
  ];

  // ---- tokens (word-level, after the phrase pass) --------------------------------------------------------
  const MES = {ene: "Jan", feb: "Feb", mar: "Mar", abr: "Apr", may: "May", jun: "Jun", jul: "Jul", ago: "Aug", sep: "Sep", oct: "Oct", nov: "Nov", dic: "Dec"};
  // \b does not work next to accented letters ("Último"), so word edges use Unicode letter lookarounds.
  // Built at runtime so a browser without lookbehind (Safari < 16.4) falls back to \b instead of a SyntaxError.
  const W = (w, notAfter = "") => {
    try { return new RegExp(`${notAfter ? `(?<!${notAfter})` : ""}(?<![\\p{L}\\d])${w}(?![\\p{L}\\d])`, "gu"); }
    catch { return new RegExp(`\\b${w}\\b`, "g"); }
  };
  const TOKENS = [
    [/\b(\d{1,2}) (ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\b/g, (_, d, m) => `${d} ${MES[m]}`],
    [W("FGe"), "eGFR"], [W("CAC"), "ACR"], [W("ERC", "PROT-AP "), "CKD"],   // not in the protocol's name, PROT-AP ERC
    [W("Último"), "Last"], [W("último"), "last"],
    [W("sin N18"), "no N18"], [W("sin"), "without"], [W("Sin"), "No"],
    [W("meses"), "months"], [W("mes"), "month"], [W("años"), "years"], [W("días"), "days"],
    [W("valores"), "values"], [/ el (?=\d{4}-\d{2}-\d{2}|\d{1,2} (?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b)/g, " on "],
    [W("pac\\."), "pts"], [W("paciente"), "patient"], [W("Diabetes tipo 2"), "Type 2 diabetes"],
    [W("Hipertensión"), "Hypertension"], [W("Mujer"), "Woman"], [W("Hombre"), "Man"],
    [W("Hoy"), "Today"], [W("hoy"), "today"], [W("presencial"), "in person"],
    [W("nota del"), "note of"], [W("Nota del"), "Note of"],
  ];
  const fixNumber = n => /^\d{1,3}(\.\d{3})+$/.test(n) ? n.replace(/\./g, ",")
    : /^\d+,\d{1,2}$/.test(n) ? n.replace(",", ".") : n;

  function translatePlain(s) {
    const lead = s.match(/^\s*/)[0], trail = s.match(/\s*$/)[0];
    let t = s.trim();
    if (!t) return s;
    if (EXACT.has(t)) return lead + EXACT.get(t) + trail;
    for (const [k, v] of PHRASES) if (t.includes(k)) t = t.split(k).join(v);
    for (const [re, rep] of RULES) t = t.replace(re, rep);
    if (EXACT.has(t)) t = EXACT.get(t);
    for (const [re, rep] of TOKENS) t = t.replace(re, rep);
    t = t.replace(/\d+(?:[.,]\d+)+/g, fixNumber);
    return lead + t + trail;
  }
  // Text inside «…» is a quote from a clinical note: kept exactly as written.
  function translate(s) {
    if (!s) return s;
    if (!/[A-Za-zÁÉÍÓÚáéíóúñÑ]/.test(s)) return s.replace(/\d+(?:[.,]\d+)+/g, fixNumber);
    const parts = s.split(/(«[^»]*»)/);
    if (parts.length === 1) return translatePlain(s);
    // Translate the whole string with placeholders so phrase rules can span a quote.
    const quotes = [];
    const masked = parts.map(p => p.startsWith("«") ? (quotes.push(p), `«${quotes.length - 1}»`) : p).join("");
    // «vacía» is the rule's own word for an empty unit, not a note quote.
    return translatePlain(masked).replace(/«(\d+)»/g, (_, i) => quotes[+i] === "«vacía»" ? "«empty»" : quotes[+i]);
  }
  window.traducirAlIngles = translate;   // for tests
  // A second pass must change nothing (otherwise the observer would loop): checked by the language test.
  window.traducirEsEstable = s => translate(translate(s)) === translate(s);

  const SKIP = "script,style,[lang=es]";
  const ATTRS = ["aria-label", "title", "placeholder"];
  const written = new WeakMap();   // text node -> the value this layer wrote: never translated twice
  function walk(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      if (written.get(root) === root.nodeValue) return;
      if (root.parentElement && !root.parentElement.closest(SKIP)) {
        const t = translate(root.nodeValue);
        if (t !== root.nodeValue) { root.nodeValue = t; written.set(root, t); }
      }
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE || root.closest(SKIP)) return;
    for (const a of ATTRS) if (root.hasAttribute(a)) {
      const v = root.getAttribute(a), t = translate(v);
      if (t !== v) root.setAttribute(a, t);
    }
    for (const c of root.childNodes) walk(c);
  }
  function start() {
    const st = document.createElement("style");
    st.textContent = '.nota-original::before{content:"Original note, in Spanish · ";display:block;font-size:12px;font-weight:700;' +
      'letter-spacing:.04em;text-transform:uppercase;color:var(--suave);margin-bottom:4px}';
    document.head.appendChild(st);
    document.title = translate(document.title);
    addSwitch();
    walk(document.body);
    new MutationObserver(muts => {
      for (const m of muts) {
        if (m.type === "characterData") walk(m.target);
        else if (m.type === "attributes") walk(m.target);
        else m.addedNodes.forEach(walk);
      }
    }).observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
