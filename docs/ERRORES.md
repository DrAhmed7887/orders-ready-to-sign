# Error register

Every error found in the engine or the note checks, with its cause, its fix and where the fix was measured again.
Round 13, E4 (signed 16 Nov 2026). `tests/test_errores.py` fails if a wrong finding in a committed review CSV has no
row here. Software and real-text test errors only; no patient data.

## Note checks (real text, CodiEsp)

| ID | Found | Case (key) | What went wrong | Cause | Fix (round) | Measured again |
|---|---|---|---|---|---|---|
| E-01 | 16 Nov, dev review | `dev/S0211-69952011000400013-1#0` | ACR 261.9 mg/g not read | another urine measure in the sentence made the ACR "doubtful" | other urine measures removed first (11) | held-out: no albumin case left, **not re-measured** |
| E-02 | 16 Nov, dev review | `background/S0365-66912004000700007-5#0` | refusal of a drug read as refusal of the test | any refusal word counted | refusal must be of a test (11) | held-out: 0 wrong refusals (40 refusal-stratum cases) |
| E-03 | 16 Nov, dev review | `train/S0211-69952014000500020-1#0` | eGFR 34 not read | value more than 12 characters from "FGe" | within 60 characters if followed by ml/min (11) | held-out: no accepted eGFR finding, **not re-measured** |
| E-04 | 16 Nov, dev review | `background/S1130-01082008001200011-2#0` | "valorado por Nefrología" read as follow-up | any sentence naming Nephrology counted | follow-up word required (11) | held-out: 1 wrong of 4 accepted (E-11) |
| E-05 | 16 Nov, dev review | `background/S0376-78922008000400006-1#0` | "tras valoración por Nefrología" read as follow-up | same as E-04 | same (11) | same |
| E-06 | 16 Nov, dev review | `train/S0211-69952009000500014-1#0` | a referral read as follow-up | same as E-04 | same (11) | same |
| E-07 | 16 Nov, dev review | `train/S1134-80462015000100006-1#0` | "Nefrología confirma" read as follow-up | same as E-04 | same (11) | same |
| E-08 | 16 Nov, dev review | `train/S1137-66272011000300024-1#0` | ACR 0.6 µg/mg not read | µg/mg unit not known | µg/mg = mg/g (11) | held-out: no albumin case left, **not re-measured** |
| E-09 | 16 Nov, dev review | `test/S0211-69952014000400019-1#0` | a 2009 referral, later stopped, read as follow-up | same as E-04 | same (11) | same |
| E-10 | 16 Nov, dev review | `dev/S0211-69952009000500017-1#0` | an author affiliation line ("Instituto de Nefrología") | same as E-04 | same (11) | same |
| E-11 | 16 Nov, held-out review | `background/S0211-69952013000500032-1#0` | an admission read as follow-up because of "controlada" (about fluids) | follow-up word anywhere in the sentence | word must be in the same clause as "Nefrología", within 8 words (13, N1) | held-out 2: 8 Nephrology findings accepted, 0 wrong |
| E-13 | 16 Nov, code review of round 13 | probe sentences, not a review CSV | "Ingresó en Nefrología para control de la tensión arterial" is still accepted as follow-up | the admission veto applies only to the clinic path, not to the follow-up word | an admission word (ingres…, hospitaliz…) in the same clause cancels the follow-up word (14, signed 16 Nov) | held-out 2 (`eval/results/notas_reales_heldout2.md`): 8 Nephrology findings accepted, 0 wrong |
| E-14 | 16 Nov, held-out 2 review | `livingner_test_background/cc_reumatologia341#0` | a dipstick "albuminuria ++++" accepted as a urine ACR done | "albuminuria" names the test | fixed, round 15 V3 (signed 16 Nov) | — |
| E-15 | 16 Nov, held-out 2 review | `livingner_test_background/cc_reumatologia175#0` | "albuminuria, 4.5 g/24 h" accepted as a urine ACR done | same as E-14 | fixed, round 15 V3 (signed 16 Nov) | — |
| E-16 | 16 Nov, held-out 2 review (changed by Claude) | `livingner_test_background/caso_clinico_neurologia305#0` | "FG &gt; 60" read as exactly 60 | the eGFR value reader skips the ">" sign (corrected 16 Nov: the text has a plain ">", not the HTML entity first recorded here) | fixed, round 15 V4 (signed 16 Nov) | — |
| E-17 | 16 Nov, held-out 2 review | `caso_clinico_medicina_interna58`, `caso_clinico_medicina_interna505` | ACR 57 and 36 mg/g in the sentence, no value read | other numbers in the sentence make the value ambiguous | safe direction (no value, no effect); not fixed: V1 held after failing three blind sets | — |
| E-18 | 16 Nov, code review of round 14 | probe sentences | the admission veto is clause-wide: "Seguido en Nefrología desde su ingreso en 2015" is now rejected (safe direction); and a separate clause can still link Nephrology to a control word: "Ingresó por IRA, Nefrología controló la diuresis" is accepted | the veto ignores word order; the clause split is by punctuation only | not fixed; candidate for a later round (needs signature) | — |
| E-19 | 16 Nov, ACR recall (amendment 8) | 21 held-out 2 albumin cases | the reader pointed to a marked ACR sentence in 9 of 21 (8 naming the ACR test), the code accepted 5, and read the value in 0 | the model often answers "ninguna" or malformed JSON on long case reports; the value reader gives up when any other number stays in the sentence, even one with its own unit (20 of 24 marked sentences); "Índice albumina/creatinina" is not recognised as the ACR (corrected 16 Nov: unaccented "albumina" was already read) | naming fixed by V2 (signed 16 Nov); value reading not fixed (V1 held) | `eval/results/notas_reales_recall_acr.md` |
| E-12 | 16 Nov, recall study | 95 of 98 held-out cases with a marked finding | the reader missed 95 of 98 notes with a real finding (0 of 94 test-done notes) | the reader returns one finding per note and almost never points to a lab value in a hospital case report | none yet; a note no longer removes an eGFR order (13, R5), so these misses cannot hide an eGFR order | `eval/results/notas_reales_recall.md` |

## Engine (found by an independent review, 16 Nov; each reproduced with a probe)

| ID | What went wrong | Fix (round 13) | Test |
|---|---|---|---|
| E-20 | two abnormal lab ACRs ≥ 3 months apart got "unconfirmed: repeat" | S1d «Albuminuria persistente en dos analíticas: valorar código de ERC» (R1) | `tests/test_vuelta13.py` |
| E-21 | a dialysis patient got "Solicitar CAC"; a pregnant woman got S1b | exclusions: dialysis, transplant, palliative care, recent pregnancy (R2) | same |
| E-22 | an eGFR equation switch faked an S3 fall | one equation per trend; mixed and too few → insufficient (R3) | same |
| E-23 | I12/I13 and E11.21/E11.22 did not count as a CKD code | added to the CKD codes (R4) | same |
| E-24 | a dated note with "FGe 22" removed an eGFR order | a note never removes an eGFR order (R5) | same |
| E-25 | a negative ACR counted as a recent ACR; eGFR 5,000 accepted | impossible values → insufficient information (R6) | same |
| E-26 | the repeat order did not say which sample | first-morning midstream urine, with KDIGO Table 16 conditions (R7) | same |
| E-27 | type 1 diabetes not screened | E10 ≥ 5 years after the first code (D) | same |

## Synthetic generator

| ID | What went wrong | Fix |
|---|---|---|
| E-40 | the 1,000-patient generator drew an eGFR equation per value, so most trends mixed equations (unlike a real lab) | one equation per patient, same random draws (round 13) |
| E-41 | the generator gives "I12.9" to some hypertensive patients without kidney disease; since R4 that counts as a CKD code | not fixed: kept to keep the seed; disclosed in `data/synthetic/DATA_CARD.md` |
| E-42 | 16 Nov, round 15 blind set 2 | `eval/ciego_v15/frases_set2.csv` (sentence "Microalbuminuria por encima de 300 mg/g…") | a bound read as an ACR value of 300 mg/g, round 15 only | "por encima de" is not among the bound words; V1 removed the other-lab numbers that used to hide it | fixed, V6 (signed 16 Nov) | `eval/results/ciego_v15_set2.md` |
| E-43 | 16 Nov, round 15 blind set 2 | same set ("CAC 18 mg/g (03/05/2026); CAC 52 mg/g (14/09/2026)…") | the first of two ACRs read as the result, on round 14 and 15 | the sentence splitter cuts at "; C", so the pointed piece holds one result only | fixed, V7 (signed 16 Nov) | `eval/results/ciego_v15_set2.md` |
| E-44 | 16 Nov, round 15 blind set 1 | `eval/ciego_v15/frases_set1.csv` ("FGe CKD-EPI 2021 de 57") | the equation year read as the eGFR (2021), on round 14 too | the eGFR value reader skips letters and takes the first number | fixed, V5 (signed 16 Nov) | `eval/results/ciego_v15_set1.md` |
| E-45 | 16 Nov, code review of round 15 | probe "CAC menos de 30 mg/g, K 4 mEq/l" | a bound read as exactly 30 mg/g (abnormal), round 15 only | same as E-42 ("menos de" is not a bound word) | moot: V1 held (and V6 signed) | `docs/FIRMA_VUELTA_15.md` |
| E-46 | 16 Nov, code review of round 15 | probe "CAC 25 mg/g y CAC 450 mg/L" | the second CAC (wrong unit) hidden, 25 read, round 15 only | V1 strips every number with a non-ACR unit, even right after a CAC name | moot: V1 held | `docs/FIRMA_VUELTA_15.md` |
| E-47 | 16 Nov, round 15 blind set 3 | `eval/ciego_v15/frases_set3.csv` ("CAC 2 mg/mmol o menos, urea 29 mg/dl") | a bound written after the number read as the value, round 15 only | "o menos / o más" after the number is not a bound word; V1 removed the urea number that used to block it | moot: V1 held | `eval/results/ciego_v15_set3.md` |
| E-48 | 16 Nov, round 15 blind set 3 | same set ("FGe más de 60", "FGe … por encima de 60") | an eGFR bound in words read as the value, rounds 14 and 15 | V4's bound words lack "más de" and "por encima/debajo de" | not fixed; grey line only; candidate for the next round | `eval/results/ciego_v15_set3.md` |
| E-49 | 16 Nov, round 15 blind set 3 | same set ("CAC 14 mg/g (07/07/2021); CAC 14 mg/g (07/01/2022)") | two equal results read as one value (no date), rounds 14 and 15 | the value reader keeps distinct values only | not fixed; no date, so it can remove nothing | `eval/results/ciego_v15_set3.md` |
| E-50 | 16 Nov, code review of amendment 14 | probe "CAC 25 mg/g y ACR 450 mg/L el 03/03/2026" | the second result hidden, 25 mg/g read with a date, round 15 only | V1 keeps a wrong-unit number only after "CAC" or "albúmin…" within 25 characters | moot: V1 held | `docs/FIRMA_VUELTA_15.md` |
