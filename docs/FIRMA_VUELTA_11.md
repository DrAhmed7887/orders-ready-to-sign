# Note checks, round 11: for Ahmed's signature

> **Status: signed by Ahmed Zayed (MB BCh), 16 Nov 2026** ("Signed, run held-out"), as written, with the default
> for each open choice below. Changes after this go in a new round.

## Where they come from
The real-text test (`eval/results/notas_reales.md`) ran 300 real published Spanish case reports (CodiEsp). The code
accepted 20 findings and 10 were wrong. An AI agent reviewed them and Claude re-read all 20. Each change below fixes
one of those errors. None of the 10 could change an order, because refusal and Nephrology findings only add a grey
line and undated "test done" findings remove nothing. In dated primary-care notes they could.

## The five changes

| # | Rule | Before | Proposed | Real case behind it |
|---|---|---|---|---|
| 1 | **N1c "followed in Nephrology"** | any sentence that mentions "nefrolog…" | the sentence must say follow-up or control (seguimiento, seguido/a, controlado/control, revisiones), **or** name a clinic (consultas, policlínico, hospital de día) without being a referral or an assessment (derivado, remitido, envían, valorado, valoración, interconsulta, confirma, ingresa) | 7 of 14 were "valorado por", "tras valoración", "la envían a", "Nefrología confirma", "derivado a consulta" and an author affiliation line |
| 2 | **N1b refusal** | any refusal word | not accepted if what is refused is a treatment, drug, surgery, admission, dialysis, vaccine, biopsy, transplant or immunosuppressant **and** the sentence names no test (orina, muestra, analítica, CAC, cociente, sangre, FGe…) | "rechazo del paciente a otro tratamiento inmunosupresor" |
| 3 | **N1a ACR value, units** | µg/mg not recognised, so no value is read | µg/mg (also mcg/mg, ug/mg, µg/mgr) is read as the same number in mg/g | "Cociente albúmina/creatinina: 0,6µg/mgr" |
| 4 | **N1a ACR value, other urine measures** | any other number in the sentence makes the ACR "doubtful" | a proteinuria or proteinuria/creatininuria value is removed before the ACR is read, so it neither blocks the ACR nor gets read as one | "índice microalbuminuria/creatininuria de 261,9 mg/g y proteinuria/creatininuria 1,1" |
| 5 | **N1a eGFR value** | the value must be within 12 characters of "FGe"/"filtrado" | the same, **or** within 60 characters when it is followed by "ml/min" | "filtrado glomerular estimado (FGe) MDRD (Modification of Diet in Renal Disease) 34ml/min/1,73m2" |

Not changed on purpose: the hidden-instruction filter discarded one real note ("La UCI clasifica el cuadro como
APACHE II"). That fails safe: the note is ignored. Loosening a safety filter to fit one example is the wrong trade.

## Open choices for you
1. **"Derivada a consultas de Nefrología para seguimiento"** is accepted as followed, because it says follow-up. Do
   you want a referral to count only once follow-up has actually happened?
2. **Inpatient care** ("continúa hospitalizada para proseguir sus controles", with Nephrology co-managing) is
   accepted, because of "controles". Should only outpatient follow-up count?
3. **µg/mg = mg/g** is the same number (µg albumin per mg creatinine). Confirm.
4. A referral sentence for someone later followed (case 10, "remitida al servicio de Nefrología") is now rejected.
   That is a miss in the safe direction: the patient stays on the list.

## What was checked (software verification, not an evaluation)
- **New tests:** `tests/test_notas_v11.py`, 25 tests, built from each real error sentence plus near-misses that must
  still pass. They include negated follow-up, two different ACRs (still ambiguous), proteinuria in mg/g (not read as
  an ACR), and an eGFR far from its name with no unit (not read).
- **Existing tests:** all pass, 594 in total.
- **Synthetic note sets, unchanged:** notas_dev and aguja (oracle outputs and recorded Qwen outputs), the 1,000-patient
  list (oracle and Qwen), and the stress loop.
- **Replay of the real recording:** the 10 wrong findings are all fixed. Seven are now rejected, and three now read
  261.9 mg/g, 34 and 0.6 mg/g. One "correct" finding is now rejected (choice 4). No new finding is accepted.

**This replay is not a result.** The changes were written from these same 300 cases, so re-scoring them would
overstate the fix. The honest measure is a **fresh held-out sample**: 300 new CodiEsp cases from the 3,451 not yet
used, with the same strata and seed rule. It would be run once with the signed checks, and reviewed the same way, by
the agent and then you. Cost is about $0.25 of Modal grant credit and needs your OK for that run.
