"""Every wrong finding in a committed review CSV has a row in docs/ERRORES.md (round 13, E4)."""
import csv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REGISTER = (ROOT / "docs/ERRORES.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["revision_agente.csv", "revision_agente_heldout.csv", "revision_agente_heldout2.csv"])
def test_every_wrong_finding_is_registered(name):
    with (ROOT / "eval/notas_reales" / name).open(encoding="utf-8", newline="") as fh:
        wrong = [r["key"] for r in csv.DictReader(fh) if r["verdict"] != "correct"]
    assert wrong
    for key in wrong:
        assert f"`{key}`" in REGISTER, key
