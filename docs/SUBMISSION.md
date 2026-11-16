# Submission text (AI for Medicine, Devpost)

Source for the Devpost "written description" field. Every number comes from the README, which is checked against
`eval/results/*.json` by `tests/test_readme_claims.py`; this file repeats README numbers only.
Required sections (rules page, read 15 Nov 2026): problem and who has it · method · Evaluation · Who benefits, and who
could be harmed · limitations · another month. Attribution and AI-tool disclosure at the end.

---

## Orders ready to sign: signs of kidney damage hiding behind a normal blood test

**1 in 7 people with diabetes or high blood pressure have signs of kidney damage hiding behind a normal blood test. 19 in 20 of them have never been told.** Every morning, this tool reads a family doctor's list, finds those people, and prepares the next test for the doctor to sign.

### The problem, and who has it
Amparo is 69, with type 2 diabetes and high blood pressure. Her blood test (eGFR 68) looks acceptable. But a urine test found albumin (85 mg/g; normal is under 30), and a second high result came in a letter from her insurer, typed into a note where no filter looks. She has no kidney diagnosis and is not on the medicine that also protects the kidneys. *(Amparo is synthetic; the numbers below are real.)*

On US national data (NHANES, CDC; survey-weighted, 95 % CI):
- **143 per 1,000** adults with diabetes or high blood pressure have urine albumin ≥ 30 mg/g with eGFR ≥ 60 (128–159; 2021–2023, n = 2,216).
- **953 per 1,000** of them were never told they have weak or failing kidneys (904–977).
- **218 per 1,000** of adults with diabetes, hypertension and albumin ≥ 30 mg/g behind an eGFR ≥ 60 were taking no ACE inhibitor or ARB (151–304; 2017–2020), the treatment KDIGO 2022 Rec. 1.2.1 recommends for this group (includes people who may have a reason not to take one).

Spain has the same gap: 54 % of CKD in adults with type 2 diabetes in Spanish primary care was undiagnosed, mainly with isolated eGFR or ACR abnormalities (DIAMOND2, 2026). The people who have the problem: the patient, who doesn't know, and the family doctor, who has no time to re-read every chart every morning.

### Method
- **Rules, not a prompt.** Signed SQL rules over an OMOP-shaped primary-care extract: S1a (type 2 diabetes, hypertension or eGFR < 60 with no urine ACR in > 12 months), S1b (abnormal ACR not repeated in > 6 months, no CKD code), S1c (two abnormal ACRs ≥ 3 months apart, one from a note: consider a CKD code), S3/S3c (falling eGFR). Sources: KDIGO 2012/2024 and the Valencian primary-care protocol. Every threshold lives in one table.
- **Suppression.** A test already ordered or recently repeated is not listed again; a missing value or unknown unit is never treated as normal.
- **A small open model, held in check.** Qwen3-4B-Instruct-2507 reads free-text notes for results typed there. It only points to a numbered sentence; the code copies that sentence, rejects negations, plans, family members and reference values, and reads the value and date itself. The rules decide.
- **The doctor signs.** Each order comes with its reason, the numbers, the dates and a review date. One click to sign, or dismiss with a reason. It never proposes a drug, and the diagnosis stays with the doctor: for persistent albuminuria it only asks the doctor to consider recording a CKD code. In this prototype the decision log stays in the browser; no order is transmitted.

### Evaluation
Pre-registered protocol for the primary and secondary measures (committed 23:19 and signed 23:21 on 15 Nov 2026, before the evaluation code at 23:26; later changes are dated amendments). The awareness, treatment and population figures are descriptive analyses added after the run. Each NHANES participant becomes a one-visit extract (eGFR by CKD-EPI 2021, urine ACR, diagnosed diabetes/hypertension); the unchanged rules run on it. Survey design: MEC weights, strata, PSUs, Taylor linearisation, logit CIs. Files pinned by SHA-256; no random step.

| Question | Result |
|---|---|
| Share of single-visit kidney markers found by a blood-test-only filter (last eGFR < 60) | **481 per 1,000** (445–517) |
| Adults with diabetes or hypertension with albumin behind an acceptable eGFR | **143 per 1,000** (128–159) |
| Engine's "repeat ACR" orders confirmed ≥ 30 mg/g on a second urine sample (NHANES 2009–2010, non-circular) | **524 per 1,000** (441–606; n = 360) |
| Figures in the CDC's own analytic note for the 2009–2010 urine file | **7 of 8 reproduced exactly** (the 8th explained) |

What it means: on a single visit, the engine's ACR threshold and the albuminuria reference are the same, so "the engine flags them" checks the pipeline on real values; it is not an accuracy claim. The findings are the size of the gap and the confirmation rate: about half of repeat orders confirm, which is why the tool asks for a repeat, not a diagnosis.

Software verification on synthetic data (labels written before running): a 1,000-patient synthetic Spanish list, 1,000 / 1,000 correct with 0 false alerts and 0 missed (a blood-test-only filter: 49 false alerts, 107 missed); 23 / 23 hard cases; note reader 12 / 12 and 6 / 6 with 0 wrong exclusions. This verifies the code against the signed rules; it is not clinical validation.

**Reproduce:** `pip install -r requirements-eval.txt && python3 eval/nhanes/fetch.py && python3 eval/nhanes/run.py && python3 eval/nhanes/people.py`

### Who benefits, and who could be harmed
- **Benefits:** people like Amparo, found while their kidney damage can still be slowed; family doctors, whose checking is done before the clinic opens.
- **Extra tests:** about half of repeat orders will come back normal (a second sample, some worry, a small cost).
- **False reassurance:** not being on the list is not "cleared"; the tool sees only the record.
- **Wrong setting:** the evidence is from the US; the tool is designed for Spanish primary care. A rule error would affect a whole list, so every rule has tests, every order shows its reason, and nothing happens without the doctor's signature.

### Limitations
Single measurements (a CKD diagnosis needs > 3 months); the second urine sample was within 10 days, not 3 months; self-reported diagnoses; about a third of eligible people had no lab values (complete cases); synthetic sets and labels generated by the AI assistant that also wrote the rules (not blind); the blood-test-only filter is a hypothetical baseline, not current practice; type 1 diabetes only from 5 years after its first code; prototype, not connected to any record system. On real published Spanish case reports the note reader is safe but weak: on new text 3 of 25 accepted findings were wrong and none could change an order (round 15 removed two and turned the third into a bound note, and added two new unreviewed grey lines; checked on the same text, so not a new test), but it found an ACR result in 5 of 21 cases and read none of their values, so the persistence path (Amparo's) was shown on synthetic notes only. Reviews of real-text findings were by an AI agent, not a physician.

### What we would do with another month
1. A blind test with an independent family doctor labelling 200 synthetic charts.
2. Apply for access to a Spanish primary-care research database and measure the gap on Spanish data.
3. Measure persistence with two ACRs ≥ 3 months apart in longitudinal data.
4. A read-only pilot in one health centre: orders signed, dismissed (and why), confirmed.
5. Run the FHIR R4 reader (built, synthetic bundles only) on a real test export, and write signed orders back as FHIR ServiceRequest.

### Attribution and AI tools
Data: NHANES (CDC/NCHS, public). Guidelines: KDIGO 2012, 2022, 2024; Valencian PROT-AP ERC 2025; CKD-EPI 2021 (Inker et al., NEJM 2021). Evidence cited: Matsushita et al., Lancet 2010; DIAMOND2, Prim Care Diabetes 2026. Models: Qwen3-4B-Instruct-2507 (Apache-2.0, run on Modal), Qwen 3.8 27B as a comparison reader. Libraries: Python standard library, SQLite, pytest, pandas, SciPy, playwright-core; vLLM 0.11.0 and Hugging Face Transformers 4.57.1 serve the note reader (weights from Hugging Face, run on Modal). AI tools: Claude (Anthropic) wrote most of the code, analysis scripts and documentation under the author's direction; GPT-6.1 Sol and Claude sub-agents reviewed the code and attacked the note checks. Every clinical rule and threshold was chosen and signed by the author (a physician), who can explain each one. First prototyped at a hackathon in Spain (13–15 Nov 2026); the evaluation and English version were built afterwards.
