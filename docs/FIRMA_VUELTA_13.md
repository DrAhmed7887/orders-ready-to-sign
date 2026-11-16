# Round 13: cutting the errors, for Ahmed's signature

> **Status: signed by Ahmed Zayed (MB BCh), 16 Nov 2026** ("Signed, defaults"), with the default for each open
> choice (A keep 30; B accept the safe-direction miss; C no age cut-off; D add E10 after its source is verified;
> E keep; F not in this round). The Modal run in E2 still needs its own OK. Numbered 13 because `docs/REGLAS.md`
> already has a "Vuelta 12".

Three inputs:
- the error table (amendment 9);
- an independent **gap-finder** agent that checked the data and the rules against KDIGO 2024 and 2022, reading the kdigo.org PDFs;
- an independent **code reviewer**.

Claude reproduced each engine finding below with a probe, which ran synthetic patients through the unchanged engine on 16 Nov 2026. Guideline quotes marked † were read by the gap-finder in the kdigo.org PDF and not re-read by Claude.

## Where the errors are (from the error table, amendment 9)

NHANES 2009–2010, 1,933 people with a second urine sample (`eval/results/nhanes_errors.md`). Counts are unweighted.

**False alarms: 158 of the 360 repeat orders came back < 30 mg/g.** They sit just above the threshold:

| First ACR (mg/g) | People | Confirmed on the 2nd sample | False alarms |
|---|---|---|---|
| 30–44 | 89 | 14 (16 %) | 75 |
| 45–59 | 47 | 19 (40 %) | 28 |
| 60–99 | 68 | 36 (53 %) | 32 |
| 100–299 | 86 | 65 (76 %) | 21 |
| ≥ 300 | 70 | 68 (97 %) | 2 |

**Misses: 28 people with a high second sample had a first ACR < 30** (18 under 20, 10 at 20–29), and 18 of the 28
second values were ≤ 50 mg/g. No rule on the first sample finds them without many more orders.

**What this means.** These are mostly not code errors. One urine sample varies, and the repeat order exists to
catch that. KDIGO 2024 asks for exactly this step: *"Confirm ACR ≥30 mg/g (≥3 mg/mmol) on a random untimed urine
with a subsequent first morning void in the morning midstream urine sample"* (Practice Point 1.3.1.2, p. S154). The
NHANES second sample was a first-morning void, so a "false alarm" here is one extra urine test that did its job.

**Moving the threshold trades one error for the other** (survey-weighted, per 1,000 people on the list):

| Repeat if first ACR ≥ | Sensitivity | PPV | False alarms | Missed |
|---|---|---|---|---|
| 20 | 91.6 % | 39.0 % | 125.2 | 7.4 |
| **30 (now, KDIGO A2)** | **86.8 %** | **52.4 %** | **69.0** | **11.5** |
| 45 | 80.4 % | 68.4 % | 32.5 | 17.1 |
| 60 | 71.3 % | 73.7 % | 22.2 | 25.1 |

A threshold picked from this table would be tuned on the data that then grades it. The PhysioNet/CinC 2019 sepsis
challenge (Reyna et al. 2020, doi:10.1097/CCM.0000000000004145) is the warning: it scored teams on hidden data from
other hospitals, and that is where performance drops. We have no second dataset with a repeat ACR to test a new
threshold.

## Rule changes (the engine)

| # | Problem (reproduced) | Proposed default | Source |
|---|---|---|---|
| R1 | **Two abnormal lab ACRs (Jan and Jun 2024, no CKD code) get "Albuminuria sin confirmar: repetir CAC".** Persistence from two notes already works (S1c); from two lab results it does not | New rule **S1d**: two lab ACRs ≥ 30 mg/g at least 3 months apart, no normal ACR between them, no CKD code → «Albuminuria persistente en dos analíticas: valorar código de ERC (N18)». It replaces S1b for that person | KDIGO 2024 PP 1.1.3.1†: "Proof of chronicity (duration of a minimum of 3 months) can be established by: … (ii) review of past measurements of albuminuria" |
| R2 | **No exclusions:** a dialysis patient (N18.6 + Z99.2) gets "Solicitar CAC"; a pregnant woman (O24.4) gets S1b | Send these to «Fuera de la lista · Excluido» with the reason, never to the list: dialysis (Z99.2, Z49, N18.6), kidney transplant (Z94.0), pregnancy (O00–O9A), palliative care (Z51.5) | KDIGO 2024 p. S250†: "Creatinine decreases physiologically during pregnancy"; §1.1.1†: detection "should be individualized based on the person's goals of care" |
| R3 | **eGFR equations are mixed in one trend:** a lab switch from CKD-EPI to MDRD fakes an S3 fall in a stable patient, and the reverse can hide one | The S3/S3c trend uses only values from one equation, the one of the latest value. If that leaves fewer than 3 values over 12 months, S3 is not computed and the patient goes to «información insuficiente». Same-day values from different equations are no longer averaged | KDIGO 2024 PP 1.2.4.1†: "Use the same equation within geographical regions" |
| R4 | **Coded hypertensive kidney disease (I12, I13) does not count as a CKD code,** so S1b still suggests "valorar código N18" | Add I12, I13, E11.21 and E11.22 (CIE-10-ES) to the CKD code group. They also stay in HTA/DM2 for S1a | CIE-10-ES code titles |
| R5 | **A dated note saying an eGFR was done removes an eGFR-only order (S3c) whatever the value,** including a note giving eGFR 22 after a fall from 60 | A note never removes an eGFR order. It adds a grey line with the value the code read. For the CAC, the signed rule (only a normal result removes) is unchanged | Code review; `docs/REGLAS.md` second amendment covers the CAC only |
| R6 | **Impossible values are accepted:** a negative CAC counts as a recent CAC and stops S1a; an eGFR of 5,000 counts | CAC < 0, or eGFR ≤ 0 or > 200 → «información insuficiente», never an order or a removal | Data check, not a guideline |
| R7 | **The repeat order does not say which sample** | «repetir CAC en primera orina de la mañana (chorro medio)». Note: avoid it during menstruation, after hard exercise, or with a symptomatic urine infection or blood in the urine | KDIGO 2024 PP 1.3.1.2: "Confirm ACR ≥30 mg/g (≥3 mg/mmol) on a random untimed urine with a subsequent first morning void in the morning midstream urine sample"; PP 1.3.1.1; Table 16 |
| R8 | Threshold | **Unchanged at 30 mg/g** (KDIGO A2). See the trade-off table above | — |

## Note checks

| # | Problem | Proposed default | Checked by |
|---|---|---|---|
| N1 | The held-out error: "Se ingresó en Nefrología con … IRA prerrenal, …, reposición hidroelectrolítica **controlada**" was accepted as Nephrology follow-up | The follow-up word must be **in the same clause as "Nefrología" (no comma, semicolon, colon or bracket between) and within 8 words of it** | Tests from the real sentence and near-misses. A replay of the 11 accepted follow-up sentences rejects the error and keeps 9 of the 10 correct ones (the 10th is choice B). The replay is not a result: see E2 |

## Evaluation (what we measure next)

| # | What | Cost |
|---|---|---|
| E1 | **Reader recall**, the largest unknown. An AI agent reads the 300 held-out texts without the model's output and marks every sentence saying a kidney test was done, refused, or that the person is followed in Nephrology. Recall = the share the model found and the code accepted. You check a random 20. Logged as `NOTES_REAL_PROTOCOL.md` amendment 5 before labelling | $0, about 20 min of your time |
| E2 | **Fresh held-out test** of N1: 300 new CodiEsp cases (seed 20261118), excluding both samples and near-duplicates of them (the review found one held-out case that is a dev case published twice) | About $0.25 of Modal grant; **your OK for that run** |
| E3 | **NHANES non-response check** (amendment 10, descriptive): people with no second sample had a high first ACR more often (24.6 % vs 18.6 %, per the gap-finder). Re-weight for it and report whether the 52.4 % moves | $0 |
| E4 | **Error register** `docs/ERRORES.md`: every error ever found, with its cause, fix, round and where it was re-measured. A test checks that every wrong finding in a review CSV has a row | $0 |

## Open choices
- **A. Threshold:** keep 30 (recommended), or tag ACR 30–44 as lower priority (still ordered, listed after the others).
- **B. Inpatient follow-up (N1):** "continúa hospitalizada para proseguir sus controles" was accepted in round 11. N1 rejects it. That is a miss in the safe direction: the patient stays on the list. Accept?
- **C. Age:** no age cut-off (recommended; KDIGO says individualise). The doctor sees the age on every order.
- **D. Type 1 diabetes (E10):** add E10 to the S1a population (recommended). The gap-finder says KDIGO 2022 does not cover screening explicitly and points to the ADA–KDIGO consensus, which Claude has not verified. I would verify it before coding.
- **E. One abnormal ACR, then one normal ACR:** today the second (normal) result ends it, with no order. KDIGO PP 1.1.1.2† says "repeat tests to confirm"; the "2 of 3 samples" rule was not found in KDIGO 2024. Keep (recommended), or ask for a third test.
- **F. CARMEN-I** (2,000 Hospital Clínic documents, including 172 referral letters, PhysioNet v1.0.2) is the closest real Spanish clinical text. Its page says identifiers were "anonymized" and replaced with "synthetic equivalents". Access is restricted: a credentialed PhysioNet user, CITI training, the Contributor Review Health DUA 1.5.0, and a review of each study by the contributors. Ahmed's storage rule says patient-derived data goes to no cloud without asking him, so running it through the Modal reader is his decision, and the DUA's terms on online services have not been read yet. Not part of this round.

## Not changed, and why
- **The NHANES weights:** the CDC codebook says "Exam sample weights should be used for analyses" for the urine file, and no separate weight exists for the second sample (gap-finder, ALB_CR_F codebook). The MEC weight stays.
- **eGFR rounding at 60:** the reviewer found a rounding mismatch, but no NHANES participant falls in the gap (checked: 0 in both cycles).
