# Round 15: the note reader's ACR and eGFR reading, for Ahmed's signature

> **Status: V2–V7 signed by Ahmed Zayed (MB BCh), 16 Nov 2026 ("B: sign V2–V7, hold V1"). V1 held: not in the
> code.** All three blind sets failed the strict criterion with V1. On the signed code (V2–V7), re-scored after every set
> had been scored (descriptive): unsafe readings 0, 0 and 4 on sets 1–3, against 16, 21 and 28 on round 14. The 4 left
> are also made by round 14 (E-48, E-49). Drafted by Claude on 16 Nov 2026 ("Yes, draft them"; "A: fix and retest").

Errors this round addresses: E-14, E-15, E-16, E-17 and E-19 (`docs/ERRORES.md`). All five were found on held-out 2
(LivingNER, real published case reports). **Held-out 2 is now tuning data, so it cannot test these fixes.** The fresh
test is in amendment 10 of `docs/NOTES_REAL_PROTOCOL.md`.

## What is safe and what is not

A note can change the list in only two ways (`docs/REGLAS.md`, N1a and round 13 R5):
- a **normal** CAC with a date (a value < 30 mg/g, or "normal" with no value) can **remove** an S1a order;
- an **abnormal** CAC (≥ 30 mg/g) with a date ≥ 3 months after the lab one can **add** an S1c order.

Everything else only adds a grey line. So reading **more** values is where the risk lies: a value wrongly read as
< 30 could remove an order, and one wrongly read as ≥ 30 could add one. Every item below is judged on that.

## Two causes were recorded wrongly (corrected in ERRORES)

- **E-16:** the text says "FG > 60" with a plain ">", not the HTML entity "&gt;" (only 1 of the 6,000+ raw texts has
  an entity). The eGFR value reader skips the sign and reads 60.
- **E-19:** unaccented "albumina" is already read (`alb[uú]mina`). The failure is a different name: "Índice
  albumina/creatinina" and "cociente microalbúmina/creatinina" are not recognised as the ACR.

## Why no value was read (all 21 real ACR cases checked, 16 Nov)

In 20 of the 24 marked ACR sentences, the value reader gave up because **another number stayed in the sentence**
(`cifras_sueltas`). Real case reports list labs in one sentence:

> "creatinina sérica (Cr) 0.92mg/dl (FG por CKD-EPI 93ml/min, cociente albumina/creatinina 57mg/g, sedimento orina normal)"

> "orina reciente (CAC 36 mg/g y CPC 0.130 g/g) y orina de 24h (proteinuria 540 mg/24h y albumina 320.2 mg/24h)"

The rule was written for short GP notes, where a second number near the CAC usually means a second, competing
result. In a lab list, the other numbers have their own units and belong to other tests.

## Rule changes

| # | Problem (reproduced on held-out 2) | Proposed default | Safety |
|---|---|---|---|
| V1 | **A number belonging to another test blocks the ACR value** (E-17, E-19: 57 and 36 mg/g not read) | When reading the CAC only, ignore a number that carries **its own unit that is not an ACR unit**: mg/dl, g/dl, mmol/l, mEq/l, µmol/l, U/l, UI/l, ng/ml, ng/l, pg/ml, µg/l, mg/l, g/l, ml/min (/1,73 m²), cc/min, %, mg/24 h, g/24 h, /µl, /mm³, /campo, lpm, mmHg, kg, cm. Ignore "24 h" in "orina de 24 h", and a protein/creatinine ratio written as "CPC … g/g". A number **without a unit** still blocks, and two ACR values still mean "ambiguous" | The CAC value must still carry mg/g, mg/mmol or µg/mg. A stray unitless number, or a second ACR, still gives "no value". Risk: a mistyped unit hides a second ACR. Checked by the blind set |
| V2 | **The ACR is not recognised under other names** (E-19: "Índice albumina/creatinina: mayor a 50 mg/g") | Also name the CAC as "índice", "ratio" or "relación" + "albúmina/creatinina", and as "(cociente) microalbúmina/creatinina" | Naming only. The value rules (V1, bounds) are unchanged: "mayor a 50" is still not a value |
| V3 | **A dipstick or a 24-hour albumin is taken as a CAC done** (E-14 "albuminuria ++++"; E-15 "albuminuria, 4.5 g/24 h") | If the sentence gives albuminuria only as crosses (+ to ++++), "tira", or with a 24-hour or concentration unit (mg/24 h, g/24 h, mg/l, g/l, mg/dl), and names no ACR (V2 names, "CAC" or an mg/g / mg/mmol value), then it is **not a CAC**. Reject it with the reason «no es un CAC: tira reactiva, orina de 24 h o concentración» | Removes two wrong grey lines. Today these rows have no value, so they already change nothing |
| V4 | **An eGFR bound is read as a value** (E-16: "FG > 60" read as 60) | A number after >, <, ≥, ≤, "mayor/menor/superior/inferior a/de" is a bound. The eGFR value is then empty; the finding stays, with the observation «límite, no valor» | A note eGFR never removes an order (R5), so today it only puts a wrong number on a grey line |
| V5 | **An equation name with a year is read as the eGFR** (found by blind set 1: "FGe CKD-EPI 2021 de 57" → 2021; also before round 15) | "CKD-EPI 2009/2021", "MDRD-4/-6" and "Cockcroft-Gault" with a year are names, not values. "CKD-EPI 93 ml/min" and "MDRD 45" are still read as values | Grey line only (R5) |
| V6 | **A CAC bound in words is read as a value** (E-42, E-45; round 14 does it too when the sentence has no other number: "CAC por debajo de 30 mg/g" → 30) | "menos de", "más de", "por encima de", "por debajo de", "hasta", "‹", "›" before the number make the CAC unreadable | Fewer readings only |
| V7 | **Two dated CACs split by "; " read as one** (E-43: "CAC 18 mg/g (…); CAC 52 mg/g (…)" → 18 with a date) | For a "test done" finding, the CAC value and the date are read across all the pieces the splitter cut at "; ". Two results, or two dates, give no value and no date | Fewer readings only. Refusals and Nephrology are unchanged |
| — | E-18 (the order of words in the admission veto) | **Not this round** | Its error is already in the safe direction |

Default for each: adopt **only if the blind test in amendment 10 passes** (no wrong value read, no non-ACR sentence
accepted as a CAC with a value). Otherwise the item is dropped and recorded in ERRORES.

## Blind test results (amendments 10–15)

Two blind sets of 160 synthetic sentences each were written by AI agents that never saw the code or the real texts.
The model's pointing is simulated, so these test the reading rules only. "Unsafe" means a reading that could act on
the list and is wrong: a wrong CAC value, or a value or clean "normal" where none should be read; an eGFR value where
a bound is written.

| | Set 1, as run | Set 2, as run | **Set 3 (latest test)** |
|---|---|---|---|
| Unsafe readings, signed round-14 code | 14 | 21 | 28 |
| **Unsafe readings, round 15 as tested** | **1** | **2** | **5** |
| Unsafe readings, V2–V7 without V1 (computed after scoring) | — | — | 4 |
| ACR values read correctly, round 14 → 15 (of 45) | 3 → 38 | 2 → 40 | 3 → 31 |
| Not an ACR but accepted as one, round 14 → 15 | 18 → 7 | 11 → 2 | 5 → 2 |
| Result | FAIL | FAIL | **FAIL** |

**Set 3's 5 unsafe readings on round 15** (`eval/results/ciego_v15_set3.md`):
- **New, caused by V1:** "CAC 2 mg/mmol o menos, urea 29 mg/dl" is read as 2 mg/mmol. "O menos" comes after the number,
  and V1 removed the urea number that used to block the reading. The direction is right (normal either way), but the
  value is wrong.
- **Also on round 14 (4):**
  - "CAC 14 mg/g (07/07/2021); CAC 14 mg/g (07/01/2022)": two equal results are read as one value, with no date, so it
    can remove nothing.
  - Three eGFR bounds written in words that V4 does not know ("más de 90", "por encima de 60", "más de 60"). These
    are grey lines only.

After set 1, Claude fixed what it showed (V3's gap; V5; the scorer's handling of split sentences). Set 1 re-scored
afterwards gives 0 unsafe readings, but it is tuning data (`eval/results/ciego_v15_set1_tuning.md`).

**The 2 unsafe readings left on set 2:**
1. **"Microalbuminuria por encima de 300 mg/g" is read as exactly 300 mg/g. Caused by V1.** "Por encima de" is not in
   the bound words, and before V1 the other labs' numbers hid it. The clinical direction is right (≥ 30 either way),
   but the value is wrong. Candidate fix: add "por encima/debajo de", "hasta" and "más de/menos de" to the bound words.
2. **"CAC 18 mg/g (03/05/2026); CAC 52 mg/g (14/09/2026)" gives 18 mg/g. This predates round 15** (round 14 does
   the same). The sentence splitter cuts at "; C", so the piece the model points to holds only the first result. With a
   date, that piece could remove an order. Candidate fix: read the CAC across the whole sentence the splitter cut,
   not only the piece.

**Also seen, unchanged by round 15:** a "normal" ACR in a list of labs is almost never accepted (1 of 20 on set 2). That
is the signed N1a behaviour, so the reading stays in the safe direction.

## Code review of the branch (16 Nov, independent reviewer; each finding reproduced by Claude)

Found by probing the code, not by the blind sets. **V1 is not safe to sign as written:**
- **"CAC menos de 30 mg/g, K 4 mEq/l" is read as exactly 30 mg/g** (round 14: no value). A normal result becomes
  abnormal (≥ 30), which could add an order. Same cause as residual 1: V1 removed the other-lab numbers that used to
  block a bound that the code does not recognise ("menos de", "más de", "por encima/debajo de", "hasta").
- **A second CAC in a wrong unit is hidden.** "CAC 25 mg/g y CAC 450 mg/L" is read as 25, and "CAC 450 mg/g, CAC 25
  mg/dl" as 450 (round 14: no value). V1 strips any number with a non-ACR unit, even one written right after a CAC name.
- V5 gap, eGFR only (grey line): "FGe Cockcroft-Gault 90 kg 57" is read as 90 (round 14: no value).
- No unit tests for V1–V5 yet, and no blind sentence carried a date, so removal and addition by date were never exercised.

The reviewer found no wrong value or clean "normal" introduced by V2, V3 or V4.

## What it would change on held-out 2 (tuning data, for orientation only, not a test)

This is a replay of the committed recording, with no new model run (`eval/results/vuelta15_tuning.md`). ACR recall is
**7 of 21** (was 5) and values read are **1** (was 0; 57 mg/g). Without V1: 7 of 21 and 0 values. These are the cases the rules were changed for, so this is
not evidence.

## Decision for Ahmed

Three blind sets have now failed the strict criterion. The pre-registered consequence (amendment 14) is that **V1 is
not proposed this week**. V2–V7 are judged on whether any unsafe reading is theirs, and none is: without V1, set 3
leaves 4 unsafe readings, and the signed round-14 code makes all 4 of them (it makes 28 in total on set 3).

- **B (recommended): sign V2–V7, hold V1.**
  - Claude then switches V1 off in the code (the other-lab numbers block the ACR value again, as in round 14) and
    re-runs every test.
  - What changes:
    - 24 of round 14's 28 unsafe readings on set 3 go away: 13 eGFR bounds, 5 eGFR equation years, and **6 split
      two-result CAC sentences** that round 14 reads as the first value **with its date** (e.g. "CAC 8 mg/g
      (15/01/2020); … 11 mg/g (16/07/2020)" → 8 mg/g on 15/01/2020). In the signed code today, such a reading could
      remove an order (E-43);
    - fewer dipstick and 24-hour grey lines;
    - more ACR names are recognised.
  - What does not change: values are still almost never read on real case reports (held-out 2 replay: 0 values).
  - The 4 unsafe readings left are all in round 14 today (E-48, E-49).
  - Code review of the amendment-14 fixes (16 Nov, reproduced by Claude) found one more V1 regression, which supports
    holding it: "CAC 25 mg/g y ACR 450 mg/L" (also "… y 450 mg/dl", "… cociente 450 mg/L") reads 25 mg/g, and with a
    date that is a normal CAC that can remove an order. Round 14, and V2–V7 without V1, give no value (E-50). The review
    found nothing unsafe in V6 or V7. Refusals and Nephrology are unchanged, and no regex is slow on 20,000-word input.
- **A again: one more fix-and-retest round for V1 and the eGFR bound words** ("o menos/o más" after the number; "más
  de / por encima de" for the eGFR), with a fourth blind set. About 1 hour. Each round so far has found a new edge case
  in V1, so another may not pass.
- ~~C. Sign all with the residuals disclosed.~~ Withdrawn: V1 can turn a normal ACR into an abnormal one (E-45, fixed
  since, but V1 keeps producing new ones: E-47).

## Not proposed

- **Fine-tuning the model so it points to more ACR sentences.** It answered "ninguna" in 7 of the 21 and gave no valid answer in 4. Every
  labelled real case is a test set, so there is nothing left to train on without contaminating the tests.
- **More real text.** No unseen ACR text is left (checked 16 Nov). Every albumin case in CodiEsp (14) and LivingNER (66)
  has been used. DisTEMIST, CANTEMIST and MedProcNER (Zenodo, CC BY 4.0) add 102 cases after de-duplication, and none
  mentions albumin. They all come from the same pool of Spanish case reports.

## What the signed code does (V2–V7, measured after signing; descriptive)

- **Blind sets, signed code** (`eval/results/ciego_v15_set{1,2,3}_signed.md`):

  | | Set 1 | Set 2 | Set 3 |
  |---|---|---|---|
  | Unsafe readings | 0 (round 14: 16) | 0 (21) | 4 (28) |
  | ACR values read correctly (of 45) | 8 (round 14: 3) | 1 (2) | 0 (3) |
  | Not an ACR but accepted as one | 2 (round 14: 16) | 2 (11) | 2 (5) |

  The scorer counts unsafe readings in set 1 with the split handling of amendment 12, so its round-14 figure is 16
  here, not the 14 of the as-run score.
- **Cost of V7, not stated before signing.** When a lab list is cut at "; ", the other labs' numbers now block the ACR
  value. Five values that round 14 read correctly are lost across sets 2 and 3, for example "CAC de 410 mg/g Cr; HbA1c
  9,2 %; …". This is the safe direction: a missed value, never a wrong one.
- **Real texts** (`eval/results/vuelta15_real_diff.md`, replayed from the recordings; these texts informed the rules):
  - Dev and held-out 1: no change.
  - Held-out 2:
    - the three wrong findings (E-14, E-15, E-16) are gone: two are rejected as not an ACR, and the "FG > 60" is now a bound;
    - two genuine ACR mentions are newly accepted as grey lines with no value ("Índice albumina/creatinina: mayor a 50 mg/g Cr";
      "cociente albúmina/creat normal").
  - ACR recall replay: 7 of 21, values read 0.
- **Synthetic demo and CI sets:** unchanged. The demo output is byte-identical, and Amparo's needle, the notes sets, the
  1,000-patient list and the stress loop all pass.

## Signature

- [x] V2 · [x] V3 · [x] V4 · [x] V5 · [x] V6 · [x] V7 · V1 held · E-18 not this round · option B
- Signed: Ahmed Zayed (MB BCh), in this session, 16 Nov 2026: "B: sign V2–V7, hold V1"
