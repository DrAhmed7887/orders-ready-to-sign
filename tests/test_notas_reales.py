"""The real-text recording covers exactly the sampled cases, and the committed results come from replaying it."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "eval/notas_reales"
MUESTRA = json.loads((HERE / "muestra.json").read_text(encoding="utf-8"))
REC = [json.loads(line) for line in (HERE / "salidas_qwen3-4b-instruct-2507.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
RES = json.loads((ROOT / "eval/results/notas_reales.json").read_text(encoding="utf-8"))


def test_recording_matches_sample():
    assert len(MUESTRA["cases"]) == 300 == len(REC)
    assert {c["sha256"] for c in MUESTRA["cases"]} == {r["sha256"] for r in REC}
    assert {r["modelo"] for r in REC} == {"Qwen/Qwen3-4B-Instruct-2507"}


def test_results_counts_are_consistent():
    assert sum(RES["model_said"].values()) == 300 and RES["missing_outputs"] == 0
    assert sum(RES["accepted_by_label"].values()) == RES["accepted_findings"]


CHECKS = __import__("hashlib").sha256((ROOT / "notas/verificar.py").read_bytes()).hexdigest()


@pytest.mark.skipif(not (HERE / "raw").exists(), reason="CodiEsp texts not downloaded (CI)")
@pytest.mark.skipif(RES.get("checks_sha256") != CHECKS,
                    reason="notas/verificar.py changed since this result; it describes the earlier checks (see checks_sha256)")
def test_replay_reproduces_results():
    before = (ROOT / "eval/results/notas_reales.json").read_text(encoding="utf-8")
    args = [sys.executable, str(HERE / "revisar.py")]
    if "primary" in RES:
        args += ["--puntuar", str(HERE / "revision_agente.csv"), "--revisor", RES["primary"]["reviewer"],
                 "--dudosos", ",".join(RES["primary"]["judgment_calls_counted_correct"])]
    subprocess.run(args, check=True, capture_output=True)
    assert (ROOT / "eval/results/notas_reales.json").read_text(encoding="utf-8") == before


def test_primary_measure_is_labelled_and_consistent():
    p = RES["primary"]
    assert "not a physician" in p["reviewer"]
    assert p["wrong_accepted_findings"] == len(p["wrong_cases"]) == sum(v for k, v in p["by_verdict"].items() if k != "correct")
    assert p["wrong_that_could_change_an_order"] + p["wrong_shown_only_as_a_grey_line_under_the_order"] == p["wrong_accepted_findings"]
    limitations = (ROOT / "docs/LIMITATIONS.md").read_text(encoding="utf-8")
    assert f"{p['wrong_accepted_findings']} were wrong ({p['per_100_notes']} per 100 notes" in limitations and "not a physician" in limitations
    assert f"{p['strict_reading_wrong']} counting three judgment calls" in limitations and "enriched for kidney terms" in limitations
    assert p["sample"].startswith("enriched")


HELD = json.loads((ROOT / "eval/results/notas_reales_heldout.json").read_text(encoding="utf-8"))
MH = json.loads((HERE / "muestra_heldout.json").read_text(encoding="utf-8"))
RH = [json.loads(line) for line in (HERE / "salidas_heldout_qwen3-4b-instruct-2507.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def test_heldout_has_no_overlap_and_matches_recording():
    assert not {c["id"] for c in MH["cases"]} & {c["id"] for c in MUESTRA["cases"]}
    assert len(MH["cases"]) == 300 == len(RH)
    assert {c["sha256"] for c in MH["cases"]} == {r["sha256"] for r in RH}


# The held-out result measures the round-11 checks (signed 16 Nov 2026). Round 13 changed notas/verificar.py after it,
# so its result stays pinned to round 11 until a new held-out sample is run (docs/FIRMA_VUELTA_13.md, E2).
ROUND11_CHECKS = "aa338bda7bd9120786788229a89e91c86dc3df9d690117612dfe2c556f4c7af3"
ROUND14_CHECKS = "5b8cd97e36d677b2a17037e10d91b8e9c0d80514fd2190817ece0f8d5275c3ef"   # held-out 2 and ACR recall were measured with these (signed) checks


def test_heldout_scored_with_the_signed_checks_and_labelled():
    assert HELD["checks_sha256"] in (CHECKS, ROUND11_CHECKS), "held-out result must describe signed checks"
    p = HELD["primary"]
    assert "not a physician" in p["reviewer"] and p["sample"].startswith("enriched")
    limitations = (ROOT / "docs/LIMITATIONS.md").read_text(encoding="utf-8")
    assert f"{p['wrong_accepted_findings']} was wrong ({p['per_100_notes']} per 100 notes" in limitations


@pytest.mark.skipif(not (HERE / "raw").exists(), reason="CodiEsp texts not downloaded (CI)")
@pytest.mark.skipif(HELD.get("checks_sha256") != CHECKS, reason="held-out result describes the round-11 checks")
def test_heldout_replay_reproduces_results():
    before = (ROOT / "eval/results/notas_reales_heldout.json").read_text(encoding="utf-8")
    p = HELD["primary"]
    subprocess.run([sys.executable, str(HERE / "revisar.py"), "--conjunto", "heldout",
                    "--puntuar", str(HERE / "revision_agente_heldout.csv"), "--revisor", p["reviewer"],
                    "--dudosos", ",".join(p["judgment_calls_counted_correct"])], check=True, capture_output=True)
    assert (ROOT / "eval/results/notas_reales_heldout.json").read_text(encoding="utf-8") == before


# --- Held-out 2 (LivingNER, round 13 E2 + round 14; notes protocol amendment 7) --------------------------------
H2 = json.loads((ROOT / "eval/results/notas_reales_heldout2.json").read_text(encoding="utf-8"))
M2 = json.loads((HERE / "muestra_heldout2.json").read_text(encoding="utf-8"))
R2 = [json.loads(line) for line in (HERE / "salidas_heldout2_qwen3-4b-instruct-2507.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def test_heldout2_is_livingner_and_matches_recording():
    assert M2["source"].startswith("LivingNER") and all(c["id"].startswith("livingner_") for c in M2["cases"])
    assert len(M2["cases"]) == 300 == len(R2)
    assert {c["sha256"] for c in M2["cases"]} == {r["sha256"] for r in R2}
    earlier = {c["sha256"] for c in MUESTRA["cases"]} | {c["sha256"] for c in MH["cases"]}
    assert not {c["sha256"] for c in M2["cases"]} & earlier


def test_heldout2_scored_with_current_checks_and_in_readme():
    assert H2["checks_sha256"] == ROUND14_CHECKS, "held-out 2 measures the round 13 + 14 checks"
    p = H2["primary"]
    assert "not a physician" in p["reviewer"] and p["wrong_accepted_findings"] == len(p["wrong_cases"])
    limitations = (ROOT / "docs/LIMITATIONS.md").read_text(encoding="utf-8")
    assert f"{p['wrong_accepted_findings']} were wrong ({p['per_100_notes']} per 100 notes, 95 % CI {p['ci95_exact'][0]}–{p['ci95_exact'][1]}" in limitations


@pytest.mark.skipif(not (HERE / "raw" / "livingner_training").exists(), reason="LivingNER texts not downloaded (CI)")
@pytest.mark.skipif(H2.get("checks_sha256") != CHECKS, reason="checks changed since held-out 2")
def test_heldout2_replay_reproduces_results():
    before = (ROOT / "eval/results/notas_reales_heldout2.json").read_text(encoding="utf-8")
    p = H2["primary"]
    subprocess.run([sys.executable, str(HERE / "revisar.py"), "--conjunto", "heldout2",
                    "--puntuar", str(HERE / "revision_agente_heldout2.csv"), "--revisor", p["reviewer"],
                    "--dudosos", ",".join(p["judgment_calls_counted_correct"])], check=True, capture_output=True)
    assert (ROOT / "eval/results/notas_reales_heldout2.json").read_text(encoding="utf-8") == before
