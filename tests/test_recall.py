"""The recall figures in the README and CLAIMS come from eval/results/notas_reales_recall.json (round 13, E1)."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
R = json.loads((ROOT / "eval/results/notas_reales_recall.json").read_text(encoding="utf-8"))


def test_readme_and_claims_match():
    p = R["primary_recall_per_note"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    claims = (ROOT / "docs/CLAIMS.md").read_text(encoding="utf-8")
    claim = f"{p['k']} of {p['n']}"
    assert f"**{claim}**" in readme and f"{p['pct']} %, 95 % CI {p['ci95'][0]}–{p['ci95'][1]}" in readme
    assert claim in claims and "not a physician" in R["reference"]
    ya = R["recall_by_label"]["ya_realizada"]
    assert f"none of {ya['n']}" in readme and ya["k"] == 0


def test_physician_check_is_listed_and_pending():
    assert len(R["physician_check_marks"]) == 20 and R["physician_check"].startswith("pending")


A = json.loads((ROOT / "eval/results/notas_reales_recall_acr.json").read_text(encoding="utf-8"))


def test_acr_recall_in_readme_and_claims():
    p = A["primary_acr_recall_per_note"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"**{p['k']} of {p['n']}**" in readme and f"95 % CI {p['ci95'][0]}–{p['ci95'][1]}" in readme
    assert f"{p['k']} of {p['n']} notes" in (ROOT / "docs/CLAIMS.md").read_text(encoding="utf-8")
    assert A["accepted_with_a_value_read"] == 0 and "none of the 5 did it read the value" in readme


def test_acr_recall_is_pinned():
    p = A["primary_acr_recall_per_note"]
    assert (A["albumin_cases"], p["k"], p["n"]) == (66, 5, 21)
    assert A["model_pointed_to_a_marked_acr_sentence"]["k"] == 9 and A["of_which_model_named_the_acr_test"] == 8


@pytest.mark.skipif(not (ROOT / "eval/notas_reales/raw/livingner_test_background").exists(),
                    reason="LivingNER texts not downloaded (CI)")
@pytest.mark.skipif(__import__("hashlib").sha256((ROOT / "notas/verificar.py").read_bytes()).hexdigest()
                    != "5b8cd97e36d677b2a17037e10d91b8e9c0d80514fd2190817ece0f8d5275c3ef", reason="ACR recall was measured with the round-14 checks")
def test_acr_recall_reproduces(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("recall_acr", ROOT / "eval/notas_reales/recall_acr.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main(tmp_path / "r")
    assert json.loads((tmp_path / "r.json").read_text(encoding="utf-8")) == A
