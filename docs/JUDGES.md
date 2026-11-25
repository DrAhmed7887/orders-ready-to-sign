# Judging criteria & submission status

AI for Medicine: A Global Student Hackathon (Devpost 1310617; submitted 18 Nov 2026, editable until 5 Dec 2026). Four criteria at 25 % each; ties break toward held-out evaluation.

| Criterion | Evidence |
|---|---|
| **Technical Depth** | Signed SQL rules over an OMOP-shaped extract ([`rules/`](../rules/), [`ejecutar.py`](../ejecutar.py)); suppression & "Unknown ≠ Normal" ([`supresion.sql`](../rules/supresion.sql)); sentence-verified note guard ([`verificar.py`](../notas/verificar.py)); synthetic 1,000-patient list ([`DATA_CARD.md`](../data/synthetic/cupo_espanol_1000/DATA_CARD.md)); NHANES mapper ([`core.py`](../eval/nhanes/core.py)); synthetic FHIR R4 round-trip ([`leer_fhir.py`](../fhir/leer_fhir.py)); round-15 blind sets ([`FIRMA_VUELTA_15.md`](FIRMA_VUELTA_15.md)). |
| **Rigor & Reproducibility** | Pre-registered protocol ([`EVAL_PROTOCOL.md`](EVAL_PROTOCOL.md), [`PREREGISTRO.md`](PREREGISTRO.md)); held-out US NHANES 2021–2023 (`n=2,216`) + 2009–2010 repeat cohort (`n=1,933`, error table) with 95 % CIs ([`nhanes.md`](../eval/results/nhanes.md), [`nhanes_errors.md`](../eval/results/nhanes_errors.md)); SHA-256 files ([`MANIFEST.json`](../eval/nhanes/MANIFEST.json)); 7/8 CDC figures reproduced; one-line reproduce command + CI ([`ci.yml`](../.github/workflows/ci.yml)). |
| **Clinical Relevance & Honesty** | Patient stake via Amparo + [`THE_PROBLEM.md`](THE_PROBLEM.md) + [`nhanes_people.md`](../eval/results/nhanes_people.md); circular baseline labelled; 5-line `Limits` in [`README.md`](../README.md) + full real-text audit in [`LIMITATIONS.md`](LIMITATIONS.md); claim tests ([`test_readme_claims.py`](../tests/test_readme_claims.py), [`test_landing_claims.py`](../tests/test_landing_claims.py)) & [`CLAIMS.md`](CLAIMS.md). |
| **Demo Quality** | Live GitHub Pages landing page ([`index.html`](../index.html)) with `.sb-*` live sandbox (edit eGFR, uACR, & note live against CKD-EPI 2021, SQL rules, and `verificar.py` guards), one-click doctor's screen for Amparo ([`ui/index.html?lang=en`](../ui/index.html)), and [`workflow.svg`](workflow.svg); 1080p video ready locally. |

## Awards & submission checklist

| Item / Award | Status |
|---|---|
| Public repo & live GitHub Pages (`DrAhmed7887/orders-ready-to-sign`) | **Done** — public repo + live Pages (`index.html` `.sb-*` sandbox + `ui/index.html?lang=en`) |
| Written description, attribution & AI disclosure | **Done** — [`SUBMISSION.md`](SUBMISSION.md) & [`README.md`](../README.md) (`<= 150` lines) |
| Workflow diagrams, FHIR R4 reader & Round 13/15 signed rules | **Done** — [`workflow.svg`](workflow.svg), [`leer_fhir.py`](../fhir/leer_fhir.py), [`FIRMA_VUELTA_15.md`](FIRMA_VUELTA_15.md) |
| Video ≥ 60 s (Best Presentation) & Logo (Best Logo) | **Ready locally; owner upload** — `~/Downloads/To-Upload/Firma_v2_FINAL_1080p.mp4` & `Firma_logo.png` |
| Devpost 1310617 submission & updates | **Submitted 18 Nov** — owner clicks left: upload logo + video, refresh description/URL if needed |
| Excellence in Research & Best UI | **Done** — pre-registered NHANES (`n=2,216` + `n=1,933`); English UI + `.sb-*` sandbox Playwright-tested |
| Most Promising Venture & remaining clinical backlog | **Open** — 1-page adoption note, 7-question judge Q&A, physician check of 20 AI marks ([`hoja_revision.html`](../eval/notas_reales/hoja_revision.html)) |

## Limits (5-line summary; full trail in [LIMITATIONS.md](LIMITATIONS.md))

- **Prototype, not an EHR integration:** reads OMOP-shaped or synthetic FHIR R4 extracts; not HL7-validated, writes nothing back, omits `A10BD`.
- **Synthetic validation is not clinically blind:** synthetic charts/labels were authored by the rule-writing AI; 200-chart blind MD review is pending.
- **Cross-sectional US evidence only:** NHANES has one visit and no notes/drugs/pending orders; confirmation (52.4 %) is 10-day repeat, not 3-month CKD.
- **Low real-text note recall:** on CodiEsp/LivingNER case reports, Qwen3-4B + `verificar.py` misses most labs/dates (additive grey-line aid only).
- **Keyword-bounded note guard:** [`verificar.py`](../notas/verificar.py) blocks known injections, dipsticks, 24 h albumin, and bounds, not unseen rewordings.
