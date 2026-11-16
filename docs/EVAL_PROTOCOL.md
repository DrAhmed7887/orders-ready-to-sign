# External evaluation protocol (pre-registered) · NHANES 2021–2023

> **Status: signed by Ahmed Zayed (MB BCh), 15 Nov 2026.** The protocol body was committed (15 Nov 2026, 23:19) and signed (23:21) before the evaluation code was added (23:26); that commit is the pre-registration. Changes made after that are listed, dated, under Amendments; results live in `eval/results/nhanes.md`.

## Why this evaluation
Every number in this repo so far is measured on synthetic patients whose labels our own team wrote. That checks that the code follows the signed rules; it does not show the rules matter on real people. This protocol tests the engine on **real public lab data it has never seen**, with the rules frozen as signed on 13–14 Nov 2026.

## Question
Among adults with diagnosed diabetes or hypertension, how many have a kidney finding hidden behind an "acceptable" eGFR, which a "last eGFR < 60" filter misses, and does the engine flag them for the next step?

## Data (public, no account)
NHANES August 2021–August 2023 (CDC/NCHS), files `DEMO_L`, `BIOPRO_L`, `ALB_CR_L`, `DIQ_L`, `BPQ_L` (variable names verified on the CDC codebooks, 15 Nov 2026). `eval/nhanes/fetch.py` downloads them and records SHA-256 hashes in `eval/nhanes/MANIFEST.json`.

| Use | Variable |
|---|---|
| Age, sex, pregnancy | `RIDAGEYR`, `RIAGENDR`, `RIDEXPRG` |
| Survey design | `WTMEC2YR`, `SDMVSTRA`, `SDMVPSU` |
| Serum creatinine | `LBXSCR` (mg/dL) |
| Urine albumin-to-creatinine ratio | `URDACT` (mg/g) |
| Diagnosed diabetes | `DIQ010 == 1` |
| Diagnosed hypertension | `BPQ020 == 1` |

## Population
Age ≥ 18; diabetes or hypertension as above; not pregnant (`RIDEXPRG == 1` excluded); `LBXSCR` and `URDACT` present; `WTMEC2YR > 0`. Exclusions are counted and reported.

## Mapping into the engine (no rule changes)
Each participant becomes a one-visit extract in the repo's OMOP-shaped schema: conditions (E11 / I10), one serum creatinine-based eGFR (CKD-EPI 2021, race-free; Inker et al., NEJM 2021, doi:10.1056/NEJMoa2102953) and one ACR on the exam date. The extract's reference date is the exam date + 7 months with no later tests, no pending orders and no N18 code: "an abnormal result nobody has repeated yet". The unmodified `ejecutar.py` and `rules/` run on it.

## Index tests
1. **Baseline:** last eGFR < 60 ml/min/1.73 m² (the "acceptable analítica" filter).
2. **Engine:** any order prepared by the signed rules (S1a / S1b / S3 / S3c).

## Primary measure (descriptive, stated in clinical units)
Per 1,000 adults with diabetes or hypertension (survey-weighted, 95 % CI with strata and PSU): how many have ACR ≥ 30 mg/g with eGFR ≥ 60 (missed by the baseline), and how many of those the engine flags. Also: flags per 1,000 (the GP's workload).

**Honest limit, stated up front:** on a single visit, the engine's S1b condition and the albuminuria reference share the same threshold, so "engine flags them" is a check of the end-to-end path on real lab values (units, edge values, missing codes), **not** an accuracy claim. It sizes the gap the engine targets. S3 (needs ≥ 3 eGFR over 12 months) and the suppression logic cannot be tested on one visit.

## Secondary, non-circular measure (to confirm availability first)
If an NHANES cycle provides a second urine ACR for the same participant, measure **confirmation**: of the participants the engine flags for a repeat ACR, what share is ≥ 30 mg/g on the second sample (positive predictive value of the "repeat this" order, 95 % CI). This answers the question the S1b order actually asks. If no cycle has it, this section is dropped and the README says so.

## Comparison with a published figure
The weighted prevalence of albuminuria with eGFR ≥ 60 in adults with diabetes will be set beside a published NHANES-based estimate (source chosen and quoted before the run, in `docs/EVIDENCE.md`). A large gap is reported, not tuned away.

## When the result stops being useful
US population; self-reported diagnoses; single measurements (KDIGO requires > 3 months); about a third of the eligible group has no creatinine or ACR and is dropped (complete cases, weights not re-adjusted); in the secondary analysis, people without a second sample are dropped the same way; NHANES weights do not describe a Spanish primary-care list, which is the intended setting.

## Reproduce
`pip install -r requirements-eval.txt && python3 eval/nhanes/fetch.py && python3 eval/nhanes/run.py` → `eval/results/nhanes.json` and `eval/results/nhanes.md`. No keys; only public CDC downloads.

## Sign-off (Ahmed)
- [x] Population and exclusions
- [x] eGFR equation: CKD-EPI 2021 creatinine, race-free
- [x] Mapping (exam date + 7 months, no later tests)
- [x] Primary and secondary measures as written

## Amendments (logged, dated)
1. **15 Nov 2026, before the first run:** the secondary measure uses NHANES 2009-2010, the only cycle with a second urine ACR (`URDACT2`: first-morning void collected at home within 10 days of the exam, per the CDC codebook). Same population rules and mapping.
2. **15 Nov 2026, before the first run:** the published comparison is the CDC's own analytic note for the 2009-2010 urine file (n = 5,247 adults ≥ 20 with both samples: weighted mean ACR 23.7 and 15.9 mg/g; ACR ≥ 30 in 7.7 % and 3.4 %). It checks that our pipeline reads the files the way the CDC does. A diabetes-specific published prevalence was not chosen.
3. **15 Nov 2026:** there is no random step, so the `--seed` flag was dropped from the reproduce command.
4. **15 Nov 2026, after the first run (reporting only, no measure changed):** the published check was first computed on all adults with a first sample (n = 5,929); it now uses the CDC's subset (both samples, n = 5,247), as the note states. First run: the first-sample rate was computed on all adults with a first sample (n = 5,929: 8.1 %); the second-sample rate was already on n = 5,247 (4.7 %) and did not change.
5. **15 Nov 2026, after the first run (reporting only):** after independent code review, the published check adds the CDC's medians, a computed match column, and the alternative reading "ACR ≥ 30 on both samples" (3.36 %, which rounds to the CDC's 3.4 %). Our second-sample rate (4.7 %) does not match the CDC's wording; this is reported, not tuned. The pre-registered row "hidden albuminuria flagged by the engine" is added (1,000 per 1,000 by construction), and the baseline + engine union is labelled as true by construction.
6. **15 Nov 2026, at Ahmed's request, after the pre-registered run (descriptive only):** `eval/nhanes/people.py` adds what hidden albuminuria means for people: awareness ("ever told you had weak/failing kidneys", `KIQ022`, 2021–2023 and 2017–2020), ACR ≥ 300, the US population count, and ACE inhibitor/ARB use in the exact KDIGO 2022 Rec. 1.2.1 group (diabetes + hypertension + albuminuria), from NHANES 2017–March 2020, the last cycle with drug names. Drug matching by generic name (`PRIL`, `SARTAN`) was **signed by Ahmed on 15 Nov 2026**. These measures use adults ≥ 20 (the age the kidney questions are asked), so the hidden-albuminuria rate there is 141.8 per 1,000, against 142.8 for adults ≥ 18 in the primary table.
7. **16 Nov 2026, after the first run (wording only, logged after an independent claims audit):** after signature, three passages outside this list were edited without an amendment entry: the status line (it said "Committed before any NHANES file is downloaded"; no file in the repo timestamps the first download, so the claim now rests on commit times only), the limitations (complete cases, weights not re-adjusted, and the same rule for the second sample added) and the reproduce command (amendment 3). No measure, population or threshold changed.
8. **16 Nov 2026, descriptive, at Ahmed's request ("check against real data"):** `eval/nhanes/trace.py` runs the unchanged engine on NHANES 2009–2010 and reports which workflow steps real data exercises (extract, S1b, the prepared order) and which it cannot (note reader, S1c, suppression: NHANES has no notes, drugs or pending orders), from the engine's own output. It also traces one participant chosen by a fixed rule (diabetes + hypertension, S1b order, second sample, first ACR nearest the group median, ties lowest SEQN). The first run of that rule picked someone with eGFR 42, whom a blood-test filter already flags; the same rule restricted to eGFR ≥ 60 (the case the diagram shows) was then added. Both picks are reported in `eval/results/nhanes_trace.md`. No measure, population or threshold changed.
9. **16 Nov 2026, descriptive, at Ahmed's request, after the pre-registered run:** `eval/nhanes/errors.py` reports the full error table at the engine's operating point, as published sepsis-alert evaluations do: sensitivity, specificity, PPV, NPV, people flagged, missed and falsely alarmed per 1,000, and orders per confirmed case (Wong et al., JAMA Intern Med 2021, doi:10.1001/jamainternmed.2021.2626, external validation of the Epic Sepsis Model; Reyna et al., Crit Care Med 2020, doi:10.1097/CCM.0000000000004145, on held-out sites; Adams et al., Nat Med 2022, doi:10.1038/s41591-022-01894-0, on prospective outcomes). Same data, population and reference as the secondary measure (NHANES 2009–2010, second urine ACR ≥ 30 mg/g), and the same comparison as the primary one: the engine's S1b order, the blood-test filter (last eGFR < 60), and the two together. It also reports what the engine adds over the blood-test filter (cf. "added value over usual care" in Wong 2021). The PPV and the unweighted counts are the secondary measure's own (202 of 360). Limits, stated with the table: the engine's flag is ACR ≥ 30 on the first sample, so its sensitivity against the second sample is largely a 10-day test-retest agreement of the same measurement, not discrimination; the blood-test filter was never meant to detect albuminuria, so the comparison describes where the markers sit, not a fair head-to-head; no calibration (rules give orders, not scores); one country; no outcomes. No rule, population or threshold changed.
10. **16 Nov 2026, descriptive, signed with round 13 (E3):** people without a second urine sample had a high first ACR more often (24.6 % vs 18.6 %, unweighted). `eval/nhanes/errors.py` re-weights the respondents by the inverse of the weighted response rate in cells of first-ACR band (< 30, 30–44, 45–99, 100–299, ≥ 300 mg/g) × age band (18–39, 40–59, 60+) × diabetes and recomputes the engine's PPV, sensitivity and misses: PPV 52.8 % (44.2–61.3) against 52.4 %, sensitivity 87.4 % against 86.8 %, missed 11.4 against 11.5 per 1,000. A first version used a single "first ACR ≥ 30" cell, which cannot move the PPV (independent review); it was replaced before merge. Sensitivity analysis only; no figure was replaced.
