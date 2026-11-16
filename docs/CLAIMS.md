# Every public number, and where it comes from

Rule: a number appears in the README, the landing page, the submission, the video or a post only if it is in this
table, with a file that holds it and a command that regenerates it. The tests in the last column fail if the text
and the results drift apart.

## Results we measured

| Claim (as written publicly) | Holding file | Regenerate with | Guarded by |
|---|---|---|---|
| 143 per 1,000 (128–159) adults with diabetes or hypertension have ACR ≥ 30 with eGFR ≥ 60; "1 in 7"; n = 2,216 | `eval/results/nhanes.json` (primary) | `python3 eval/nhanes/run.py` | `tests/test_readme_claims.py`, `tests/test_landing_claims.py` |
| A blood-test-only filter finds 481 per 1,000 (445–517) single-visit kidney markers; "48.1 %"; "the other 52 %" | `eval/results/nhanes.json` (primary) | same | same |
| 524 per 1,000 (441–606; n = 360) repeat-ACR orders ≥ 30 again on a first-morning urine within 10 days (not 3-month persistence); "52.4 %"; "about half" | `eval/results/nhanes.json` (secondary) | same | same |
| 13.5 per 1,000 not flagged but high on the second sample | `eval/results/nhanes.json` (secondary) | same | same |
| 7 of 8 CDC figures reproduced exactly | `eval/results/nhanes.json` (published_check) | same | same |
| 953 per 1,000 (904–977) never told; "19 in 20"; n = 313 | `eval/results/nhanes_people.json` (2021–2023) | `python3 eval/nhanes/people.py` | same |
| 218 per 1,000 (151–304) not on an ACE inhibitor or ARB; "1 in 5"; n = 204 | `eval/results/nhanes_people.json` (2017–2020) | same | same |
| Workflow diagram, real trace: 2,112 loaded, S1b 404 (on one visit S1b = ACR ≥ 30), notes/S1c/suppression not run; median case of 82 with diabetes, hypertension, S1b and eGFR ≥ 60 (restriction added after the first pick; both in nhanes_trace.md): woman, 60s, eGFR 105, ACR 98 → 31 | `eval/results/nhanes_trace.json` | `python3 eval/nhanes/trace.py` | `tests/test_workflow_claims.py` (and `docs/diagram/build.mjs` refuses to build if the trace changes) |
| Real-text note test: 300 CodiEsp cases, 20 accepted, 10 wrong (3.33 per 100, CI 1.61–6.04), 13 counting three judgment calls; enriched sample (164 of 300 by keyword), hospital case reports; 0 could change an order; AI-agent review, not physician | `eval/results/notas_reales.json` | `python3 eval/notas_reales/revisar.py --puntuar eval/notas_reales/revision_agente.csv --revisor … --dudosos …` (values in the JSON) | `tests/test_notas_reales.py` |
| Held-out real-text test (round 11 checks): 300 fresh CodiEsp cases, 4 accepted, 1 wrong (0.33 per 100, CI 0.01–1.84; 2 strict); pre-registered (amendment 3); AI-agent review, not physician | `eval/results/notas_reales_heldout.json` | `python3 eval/notas_reales/revisar.py --conjunto heldout --puntuar eval/notas_reales/revision_agente_heldout.csv --revisor … --dudosos …` | `tests/test_notas_reales.py` |
| Error table (amendment 9, descriptive): engine sensitivity 86.8 % (81.0–91.1), specificity 92.4 % (89.9–94.4), PPV 52.4 %, missed 11.5 / false alarms 69.0 per 1,000, 1.91 orders per confirmed case; blood-test filter 32.8 % / 89.0 % / 22.1 %, 58.7 / 100.8, 4.52; both 90.2 % / 83.0 % / 33.7 %, 8.5 / 155.5, 2.97; blood-test filter misses 67.2 % (57.7–75.5) of second-sample positives, engine orders a repeat for 85.5 % (79.3–90.0) of those; n = 1,933. Engine flag and reference are the same ACR ≥ 30 test (10-day test-retest, not discrimination); the eGFR filter is not designed for albuminuria | `eval/results/nhanes_errors.json` | `python3 eval/nhanes/errors.py` | `tests/test_error_table.py` |
| Held-out 2 (LivingNER, rounds 13–14 checks): 300 cases, 25 accepted, 3 wrong (1.0 per 100, CI 0.21–2.89; 10 strict); 22 of 25 correct (15 strict); Nephrology 0 wrong of 8 (3 judgment calls); pre-registered (notes amendment 7); AI-agent review, not physician | `eval/results/notas_reales_heldout2.json` | `python3 eval/notas_reales/revisar.py --conjunto heldout2 --puntuar eval/notas_reales/revision_agente_heldout2.csv --revisor … --dudosos …` | `tests/test_notas_reales.py` |
| ACR recall on 66 held-out 2 albumin cases: 5 of 21 notes (24 %, CI 8.2–47.2); value read in 0 of 5; no dates; AI-agent reference, not physician (notes amendment 8) | `eval/results/notas_reales_recall_acr.json` | `python3 eval/notas_reales/recall_acr.py` | `tests/test_recall.py` |
| Round 15 (V2–V7, signed 16 Nov): wrong readings on three blind synthetic sets 16 / 21 / 28 (round 14) → 0 / 0 / 4; the 4 are also made by round 14; set 3 still fails the strict criterion; the sets drove the fixes, so this is a descriptive re-score, not a blind result; V1 failed all three sets and was not adopted | `eval/results/ciego_v15_set{1,2,3}_signed.md` | `python3 eval/ciego_v15/puntuar.py --set N --firmado` | `tests/test_vuelta15.py` |
| FHIR R4 reader: the six synthetic sets give identical orders after extract → FHIR → extract (also with the recorded note readers); synthetic bundles only, not validated with the HL7 validator, no real export | `tests/test_fhir.py` | `python3 -m pytest tests/test_fhir.py` | `tests/test_fhir.py` |
| Reader recall on 300 held-out CodiEsp cases: 3 of 98 notes (3.1 %, CI 0.6–8.7); Nephrology 3 of 6; test done 0 of 94; AI-agent reference, not physician | `eval/results/notas_reales_recall.json` | `python3 eval/notas_reales/recall.py` | `tests/test_recall.py` |
| Non-response check (first-ACR band × age × diabetes): engine PPV 52.8 %, sensitivity 87.4 %, missed 11.4 per 1,000 after re-weighting | `eval/results/nhanes_errors.json` | `python3 eval/nhanes/errors.py` | `tests/test_error_table.py` |
| About 10.6 million US adults (an undercount) | `eval/results/nhanes_people.json` | same | `tests/test_landing_claims.py` |
| 1,000 / 1,000 on the synthetic list; basic filter 49 false alerts, 107 missed | `eval/results/cupo_espanol_1000_qwen3-4b-instruct-2507.md` | `python3 eval/evaluar.py data/synthetic/cupo_espanol_1000/extracto.sql data/synthetic/cupo_espanol_1000/etiquetas_cupo_1000.csv --notas-grabadas data/synthetic/cupo_espanol_1000/salidas_qwen3-4b-instruct-2507.jsonl` | `tests/test_readme_claims.py` |
| 23 / 23 hard cases; note reader 12 / 12 and 6 / 6, 0 wrong exclusions | `eval/results/ciego.md`, `notas_dev_qwen3-4b-instruct-2507.md`, `aguja_qwen3-4b-instruct-2507.md` | `python3 eval/evaluar.py …` (see CI) | `tests/test_readme_claims.py`, CI |

## Facts from published sources (checked 15 Nov 2026)

| Claim | Source | Checked against |
|---|---|---|
| ACR ≥ 10 mg/g predicts mortality independently of eGFR (105,872 people, 14 cohorts) | Matsushita et al., Lancet 2010;375:2073-81, doi:10.1016/S0140-6736(10)60674-5 | PubMed abstract |
| "We recommend that treatment with an ACEi or an ARB be initiated in patients with diabetes, hypertension, and albuminuria … (1B)" | KDIGO 2022 Diabetes in CKD, Rec. 1.2.1, Kidney Int 2022;102(5S):S1-S127, doi:10.1016/j.kint.2022.06.008 | guideline PDF (kdigo.org) |
| 54 % of CKD undiagnosed in 5,009 adults with T2D in Spanish primary care, "mainly in patients with isolated eGFR or uACR abnormalities" | DIAMOND2, Prim Care Diabetes 2026;20(3):298-305, doi:10.1016/j.pcd.2026.02.007 | PubMed abstract |
| CKD-EPI 2021 equation (race-free) | Inker et al., NEJM 2021, doi:10.1056/NEJMoa2102953; formula as published by the NKF | PubMed record; kidney.org |
| Epic Sepsis Model external validation: report sensitivity, PPV, alert burden and value over timely usual care (AUC 0.63; missed 67 % of sepsis; alerts on 18 % of hospitalisations) | Wong et al., JAMA Intern Med 2021, doi:10.1001/jamainternmed.2021.2626 | PubMed record (16 Nov 2026) |
| PhysioNet/CinC Challenge 2019: utility score, hidden test sets from three hospital systems, generalisation gap | Reyna et al., Crit Care Med 2020, doi:10.1097/CCM.0000000000004145 | PubMed record (16 Nov 2026) |
| TREWS: prospective multi-site study tying alerts confirmed by clinicians to outcomes | Adams et al., Nat Med 2022, doi:10.1038/s41591-022-01894-0 | PubMed record (16 Nov 2026) |
| CDC analytic note, NHANES 2009–2010 ALB_CR_F (n = 5,247; means 23.7 / 15.9 mg/g; 7.7 % / 3.4 %) | CDC/NCHS codebook ALB_CR_F | CDC page |

## Illustrative, not measured

Amparo (69, ACR 85 then 110 mg/g, eGFR 72 → 68, metformin only, appointment at 10:20) is synthetic patient 251 in
`data/synthetic/aguja/extracto.sql`. Every page that shows her says she is made up.
