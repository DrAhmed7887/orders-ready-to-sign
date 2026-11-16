"""Every number on the landing page (index.html) must match the committed evaluation results (CLAIMS rule)."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
TEXT = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", HTML))
NH = json.loads((ROOT / "eval/results/nhanes.json").read_text())
PE = json.loads((ROOT / "eval/results/nhanes_people.json").read_text())

P = NH["primary"]["per_1000_adults_with_diabetes_or_hypertension"]
HIDDEN = next(v for k, v in P.items() if k.startswith("albuminuria_behind"))
FOUND = NH["primary"]["share_of_kidney_markers_found (per 1000 with a marker)"]["baseline_eGFR<60_only"]
SEC = NH["secondary"]
CONFIRMED = next(v for k, v in SEC.items() if k.startswith("repeat_orders_confirmed"))
MISSED = next(v for k, v in SEC.items() if k.startswith("missed_by_single_test"))
TOLD = PE["2021_2023"]["never_told_weak_or_failing_kidneys_per_1000_hidden"]
RAS = next(v for k, v in PE["2017_2020"].items() if k.startswith("not_on_acei_or_arb"))


def r(x):
    return str(int(round(x)))


@pytest.mark.parametrize("claim", [
    f"{r(HIDDEN['per_1000'])} per 1,000 (95 % CI {r(HIDDEN['ci95_lo'])}–{r(HIDDEN['ci95_hi'])})",
    f"n = {HIDDEN['n']:,}",
    f"{r(TOLD['per_1000'])} per 1,000 (95 % CI {r(TOLD['ci95_lo'])}–{r(TOLD['ci95_hi'])})",
    f"n = {TOLD['n']}",
    f"{r(RAS['per_1000'])} per 1,000 (95 % CI {r(RAS['ci95_lo'])}–{r(RAS['ci95_hi'])})",
    f"n = {RAS['n']}",
    f"{r(FOUND['per_1000'])} per 1,000; {r(FOUND['ci95_lo'])}–{r(FOUND['ci95_hi'])}",
    f"{r(CONFIRMED['per_1000'])} per 1,000; {r(CONFIRMED['ci95_lo'])}–{r(CONFIRMED['ci95_hi'])}; n = {CONFIRMED['n']}",
    f"{MISSED['per_1000']} per 1,000",
    f"{PE['2021_2023']['us_adults_with_hidden_albuminuria_millions']} million",
])
def test_number_matches_results(claim):
    assert claim in TEXT, f"landing page does not say «{claim}» (results changed?)"


def test_rounded_headlines_follow_the_estimates():
    assert round(1000 / HIDDEN["per_1000"]) == 7          # "1 in 7"
    assert round(TOLD["per_1000"] / 50) == 19             # "19 in 20"
    assert round(1000 / RAS["per_1000"]) == 5             # "1 in 5"
    assert f"{r(FOUND['per_1000'] / 10)} %" in TEXT       # "48 %"
    assert f"{r(CONFIRMED['per_1000'] / 10)} %" in TEXT   # "52 %"
    published = {k: v for k, v in SEC["published_check"].items() if isinstance(v, dict)}
    assert f"{sum(v['matches'] for v in published.values())} of {len(published)}" in TEXT   # "7 of 8"
