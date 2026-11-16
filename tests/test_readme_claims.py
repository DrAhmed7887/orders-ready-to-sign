"""Numbers in README.md and docs/SUBMISSION.md must match the committed results (CLAIMS rule)."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NH = json.loads((ROOT / "eval/results/nhanes.json").read_text())
PE = json.loads((ROOT / "eval/results/nhanes_people.json").read_text())
P = NH["primary"]["per_1000_adults_with_diabetes_or_hypertension"]
HIDDEN = next(v for k, v in P.items() if k.startswith("albuminuria_behind"))
FOUND = NH["primary"]["share_of_kidney_markers_found (per 1000 with a marker)"]["baseline_eGFR<60_only"]
CONF = next(v for k, v in NH["secondary"].items() if k.startswith("repeat_orders_confirmed"))
MISSED = next(v for k, v in NH["secondary"].items() if k.startswith("missed_by_single_test"))
TOLD = PE["2021_2023"]["never_told_weak_or_failing_kidneys_per_1000_hidden"]
RAS = next(v for k, v in PE["2017_2020"].items() if k.startswith("not_on_acei_or_arb"))
PUB = {k: v for k, v in NH["secondary"]["published_check"].items() if isinstance(v, dict)}
r = lambda x: str(int(round(x)))  # noqa: E731

CLAIMS = [
    f"**143 per 1,000** adults ({r(HIDDEN['ci95_lo'])}–{r(HIDDEN['ci95_hi'])})",
    f"**{FOUND['per_1000'] / 10:.1f} %** (95 % CI {FOUND['ci95_lo'] / 10:.1f}–{FOUND['ci95_hi'] / 10:.1f} %)",
    f"**{CONF['per_1000'] / 10:.1f} %** ({CONF['ci95_lo'] / 10:.1f}–{CONF['ci95_hi'] / 10:.1f} %)",
    f"{r(HIDDEN['per_1000'])} per 1,000; {r(HIDDEN['ci95_lo'])}–{r(HIDDEN['ci95_hi'])}; 2021–2023, n = {HIDDEN['n']:,}",
    f"{r(TOLD['per_1000'])} per 1,000; {r(TOLD['ci95_lo'])}–{r(TOLD['ci95_hi'])}; n = {TOLD['n']}",
    f"{r(RAS['per_1000'])} per 1,000; {r(RAS['ci95_lo'])}–{r(RAS['ci95_hi'])}; 2017–2020, n = {RAS['n']}",
    f"**{r(FOUND['per_1000'])} per 1,000** ({r(FOUND['ci95_lo'])}–{r(FOUND['ci95_hi'])})",
    f"**{r(CONF['per_1000'])} per 1,000** ({r(CONF['ci95_lo'])}–{r(CONF['ci95_hi'])}; n = {CONF['n']})",
    f"{MISSED['per_1000']} per 1,000",
    f"**{sum(v['matches'] for v in PUB.values())} of {len(PUB)} reproduced exactly**",
]


@pytest.mark.parametrize("claim", CLAIMS)
def test_readme_numbers(claim):
    assert claim in (ROOT / "README.md").read_text(encoding="utf-8"), claim


def test_headline_fractions():
    assert round(1000 / HIDDEN["per_1000"]) == 7 and round(TOLD["per_1000"] / 50) == 19 and round(1000 / RAS["per_1000"]) == 5


def test_synthetic_counts_match_result_files():
    res = ROOT / "eval/results"
    for f, claim in [("cupo_espanol_1000_qwen3-4b-instruct-2507.md", "**1000 de 1000**"), ("ciego.md", "**23 de 23**"),
                     ("notas_dev_qwen3-4b-instruct-2507.md", "**12 de 12**"), ("aguja_qwen3-4b-instruct-2507.md", "**6 de 6**")]:
        assert claim in (res / f).read_text(encoding="utf-8"), f
    cupo = (res / "cupo_espanol_1000_qwen3-4b-instruct-2507.md").read_text(encoding="utf-8")
    fa = re.search(r"\| Falsos avisos \| 0 \| (\d+) \|", cupo).group(1)
    pe = re.search(r"\| Perdidos \| 0 \| (\d+) \|", cupo).group(1)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"{fa} false alerts · {pe} missed" in readme, (fa, pe)


SUB = [
    f"**143 per 1,000** adults with diabetes or high blood pressure have urine albumin ≥ 30 mg/g with eGFR ≥ 60 ({r(HIDDEN['ci95_lo'])}–{r(HIDDEN['ci95_hi'])}; 2021–2023, n = {HIDDEN['n']:,})",
    f"**{r(TOLD['per_1000'])} per 1,000** of them were never told they have weak or failing kidneys ({r(TOLD['ci95_lo'])}–{r(TOLD['ci95_hi'])})",
    f"**{r(RAS['per_1000'])} per 1,000** of adults with diabetes, hypertension and albumin ≥ 30 mg/g behind an eGFR ≥ 60 were taking no ACE inhibitor or ARB ({r(RAS['ci95_lo'])}–{r(RAS['ci95_hi'])}; 2017–2020)",
    f"**{r(FOUND['per_1000'])} per 1,000** ({r(FOUND['ci95_lo'])}–{r(FOUND['ci95_hi'])})",
    f"**{r(CONF['per_1000'])} per 1,000** ({r(CONF['ci95_lo'])}–{r(CONF['ci95_hi'])}; n = {CONF['n']})",
    f"**{sum(v['matches'] for v in PUB.values())} of {len(PUB)} reproduced exactly**",
]


@pytest.mark.parametrize("claim", SUB)
def test_submission_numbers(claim):
    assert claim in (ROOT / "docs/SUBMISSION.md").read_text(encoding="utf-8"), claim
