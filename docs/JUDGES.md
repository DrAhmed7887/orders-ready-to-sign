# Where each judging criterion is answered

AI for Medicine: A Global Student Hackathon (Devpost). Criteria and rules copied from the event page on 15 Nov 2026.
Four criteria at 25 % each; ties break toward the stronger held-out evaluation.

| Criterion (word for word) | Where the evidence is |
|---|---|
| **Technical Depth.** "Is there a real pipeline behind the interface? Signal processing, fine-tuning, a custom dataset, or a retrieval or inference strategy all count. A prompt and a UI with no evaluation do not." | Signed SQL rules over an OMOP-shaped extract ([`rules/`](../rules/), [`ejecutar.py`](../ejecutar.py)); suppression and "Unknown ≠ Normal" ([`rules/supresion.sql`](../rules/supresion.sql)); note reader where the model only points to a sentence and the code verifies it ([`notas/verificar.py`](../notas/verificar.py)); custom synthetic Spanish primary-care list with a data card ([`data/synthetic/cupo_espanol_1000/DATA_CARD.md`](../data/synthetic/cupo_espanol_1000/DATA_CARD.md)); NHANES mapping into the same engine ([`eval/nhanes/core.py`](../eval/nhanes/core.py)); a FHIR R4 reader feeding the same rules, synthetic bundles only ([`fhir/leer_fhir.py`](../fhir/leer_fhir.py), identical orders after the round trip on all six synthetic sets, [`tests/test_fhir.py`](../tests/test_fhir.py)); three blind synthetic sets for the note-reading rules ([`FIRMA_VUELTA_15.md`](FIRMA_VUELTA_15.md)). |
| **Rigor & Reproducibility.** "Use a held-out evaluation and report a metric in clinical units or a stated cost. Include seeds, configurations, and code. Can a stranger rerun your evaluation and understand any differences?" | Pre-registered protocol for the primary and secondary measures, with commit times and dated amendments; the people-level figures marked as post-hoc ([`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md)); held-out public data the rules never saw (NHANES), results per 1,000 adults with 95 % CIs ([`eval/results/nhanes.md`](../eval/results/nhanes.md)); files pinned by SHA-256 ([`eval/nhanes/MANIFEST.json`](../eval/nhanes/MANIFEST.json)); no random step; the CDC's own published figures reproduced (7 of 8, the 8th explained); one-line reproduce command in the README; CI on every push ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)). |
| **Clinical Relevance & Honesty.** "Address a real problem and scope your project to what it can support. Name the limitations and who could be harmed by an error. Your accuracy claim must match your evidence." | The problem in people's terms ([`THE_PROBLEM.md`](THE_PROBLEM.md), [`eval/results/nhanes_people.md`](../eval/results/nhanes_people.md)); the circular part of the evaluation is labelled as such and not headlined; "Who benefits, and who could be harmed", limitations and "when it stops being useful" in the README; every public number tested against the results ([`tests/test_readme_claims.py`](../tests/test_readme_claims.py), [`tests/test_landing_claims.py`](../tests/test_landing_claims.py)); sources checked on PubMed or the guideline PDF ([`CLAIMS.md`](CLAIMS.md)). |
| **Demo Quality.** "Show the project visibly working within the first 60 seconds. Make the input, process, and result understandable. A stranger must be able to follow the demonstration without installing anything." | Static landing page ([`index.html`](../index.html)) and doctor's screen ([`ui/index.html?lang=en`](../ui/index.html)), no install, offline; one click from the landing page to Amparo's prepared order; a workflow diagram traced with her case and with a real NHANES participant, marking the steps real data could not test ([`workflow.svg`](workflow.svg)); the input (two urine results, one only in a note), the process (rule + checked sentence) and the result (order to sign) on one screen. Video: open (backlog). |

## Awards (each judged by the organiser panel)

| Award | What it rewards | Our evidence |
|---|---|---|
| Grand Prize | highest combined score | all of the above |
| Excellence in Research & Reproducibility | strong evaluation, comparisons, limitations, reproducible | pre-registration, NHANES, CDC check, CI |
| Most Promising Venture | customer need, evidence of demand, path to adoption | DIAMOND2 (54 % undiagnosed in Spain); runs inside the health department's network on a nightly extract; one-page note: open (backlog) |
| Best Logo | originality, clarity, relevance | open (backlog) |
| Best User Interface | clarity, navigation, usability | doctor's screen; English mode tested on every view |
| Best Presentation | clearest explanation of project, features, results | landing page; video: open |

## Required submission items

| Item (rules page) | Status |
|---|---|
| Public repository with README, run and reproduce instructions | README done; public copy built and scanned clean (one commit, no remote: `scripts/copia_publica.py`); making it public is Ahmed's click |
| Video ≥ 60 s showing the project working end to end | done 16 Nov: 2:21, approved by Ahmed; upload is Ahmed's click |
| Written description: problem and who has it, method, Evaluation, Who benefits and who could be harmed, limitations, another month | [`SUBMISSION.md`](SUBMISSION.md) |
| Full attribution of models, datasets and code | README "Attribution"; SUBMISSION end |
| AI tools disclosed | README "Attribution" |

## Open backlog (dated; hours are estimates)

| Added | Item | Criterion | Hours | Status |
|---|---|---|---|---|
| 15 Nov | Workflow diagram (SVG + PNG) from the code | Demo, Presentation | 1.5 | done 16 Nov: [`workflow.svg`](workflow.svg), [`workflow_4x5.png`](workflow_4x5.png), numbers tested |
| 15 Nov | Logo | Best Logo | 1 | open |
| 15 Nov | Method sheet + the 7 questions judges ask, for Ahmed to rehearse ("Judges may ask what a given function does") | Technical Depth | 1 (+1 Ahmed) | open |
| 15 Nov | One-page adoption note (need, demand, path in, who pays) | Most Promising Venture | 1 | open |
| 15 Nov | Video ≥ 60 s: working within 60 s, verdict and stake in the first 10 s | Demo, Presentation | 3 (+0.5 Ahmed) | rendered 16 Nov, 2:21, real screens, the doctor signs at 32 s; watched with sound and approved by Ahmed, 16 Nov |
| 15 Nov | Reproduce from a fresh clone, no keys, network only for `fetch.py` | Rigor | 0.5 | done 16 Nov: install 11 s, fetch 8 s, compute 11 s; 796 tests pass; demo from SQL and from FHIR; results byte-identical to the committed ones, working tree clean afterwards |
| 16 Nov | Public repository: a fresh repo from ONE clean commit of a filtered copy (deny-listed names removed; the private history keeps the commit times that prove the pre-registration order, listed in `docs/PREREGISTRO.md`); this private repo is never made public; pre-publish scan clean | all | 0.5 | built 16 Nov, not published: `python3 scripts/copia_publica.py <new folder>` (leaves out the earlier-event material, refuses on any deny-list name, event word, private link or broken link; one commit under the GitHub noreply address); 794 tests pass in the copy (6 raw-text replays skip, as in CI); `prepublish_scan.py` CLEAN |
| 16 Nov | Note checks, from the real-text test (needs Ahmed's signature: clinical wording): "followed in Nephrology" must not accept a referral, a single consult or an affiliation line; a refusal must name the test; read values in "índice microalbuminuria/creatininuria … mg/g", "FGe MDRD … 34" and µg/mg | Clinical Relevance & Honesty | 2 (+0.5 Ahmed) | signed 16 Nov ([`FIRMA_VUELTA_11.md`](FIRMA_VUELTA_11.md)); held-out sample of 300: see NOTES_REAL_PROTOCOL amendment 3 |
| 16 Nov | Physician check of the 20 AI-agent verdicts (`eval/notas_reales/hoja_revision.html`) | Rigor | 0.25 Ahmed | open |
| 16 Nov | Round 12 candidate from the held-out test: the Nephrology follow-up word must refer to Nephrology ("reposición … controlada" was accepted); needs Ahmed's signature and a new held-out sample | Clinical Relevance & Honesty | 1 (+0.25 Ahmed) | done: round 13, N1, signed 16 Nov ([`FIRMA_VUELTA_13.md`](FIRMA_VUELTA_13.md)) |
| 16 Nov | Make that repository public and turn on GitHub Pages (Ahmed's click) | Demo | 0.25 | open |
| 16 Nov | Submit on Devpost, save the receipt in the Drive folder (Ahmed's click) | all | 0.5 | open |
| 16 Nov | FHIR R4 reader, synthetic bundles; reviewed twice | Technical Depth | 3 | done 16 Nov ([`fhir/leer_fhir.py`](../fhir/leer_fhir.py)) |
| 16 Nov | Round 15 reading rules, three blind sets; V2–V7 signed, V1 held | Clinical Relevance & Honesty | 4 | done 16 Nov ([`FIRMA_VUELTA_15.md`](FIRMA_VUELTA_15.md)) |
