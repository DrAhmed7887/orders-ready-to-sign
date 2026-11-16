"""Which steps of the workflow run on real data, and one real participant traced through the unchanged engine.

    python3 eval/nhanes/trace.py   ->  eval/results/nhanes_trace.json and .md

Descriptive (protocol amendment 8). Real data = NHANES 2009-2010 public-use files (the only cycle with a second
urine sample). Each participant becomes a one-visit extract (eval/nhanes/core.py): no notes, no drugs, no pending
orders, so the note reader, S1c and the "already ordered" suppression cannot run on it; this script reports that
from the engine's own output instead of assuming it.

Selection rule for the traced participant (fixed before running, no weights, no choice by hand): among
participants in the protocol population with diagnosed diabetes AND hypertension, an S1b order from the engine
and a second urine sample, take the one whose first ACR is closest to the median first ACR of that group;
ties -> lowest SEQN. The participant is reported by age band and rounded values only.
After the first run (16 Nov 2026) that rule picked someone with eGFR 42, whom a blood-test-only filter already
flags; the diagram's case is albumin behind an eGFR >= 60, so a second pick with the same rule restricted to
eGFR >= 60 was added. Both are reported ("any_egfr" and "egfr_60_or_more"); the diagram uses the second.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "nhanes"))

from core import extract_sql  # noqa: E402
from ejecutar import construir  # noqa: E402
from run import _engine, _load, _participants  # noqa: E402

OUT_JSON = ROOT / "eval" / "results" / "nhanes_trace.json"
OUT_MD = ROOT / "eval" / "results" / "nhanes_trace.md"
RULES = ["S1a", "S1b", "S1c", "S3", "S3c"]


def age_band(age: float) -> str:
    lo = int(age // 10 * 10)
    return f"{lo}-{lo + 9}"


def main() -> int:
    recs = _participants(_load(["DEMO_F", "BIOPRO_F", "ALB_CR_F", "DIQ_F", "BPQ_F"]), with_acr2=True)
    people, egfr, flags, base, result = _engine(recs, "nhanes_2009_2010")
    fired = Counter(p["regla"] for p in result["pedidos"])
    fired.update(t["regla"] for p in result["pedidos"] for t in p.get("tambien") or [])
    notes_read = sum(1 for p in result["pedidos"] if p.get("evolutivos"))
    removed = len(result.get("fuera_de_la_lista") or [])
    # Direct evidence: what the extract the engine ran on actually contains.
    con = construir(extract_sql(people, "nhanes_2009_2010"))
    tables = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]   # fixed names, never external input
              for t in ("note", "nota_hallazgo", "pedido_pendiente", "drug_exposure")}

    def traced(extra):
        group = [r for r in recs.values() if r["pop"] and r["dm"] and r["htn"] and flags.get(r["seqn"]) == "S1b"
                 and r["acr2"] is not None and extra(r)]
        med = statistics.median(r["acr"] for r in group)
        pick = min(group, key=lambda r: (abs(r["acr"] - med), r["seqn"]))
        order = next(p for p in result["pedidos"] if p["person_id"] == pick["seqn"])
        return {
            "group_size": len(group),
            "group_median_first_acr_mg_g": round(med, 1),
            "age_band": age_band(pick["age"]),
            "sex": "female" if pick["female"] else "male",
            "egfr": round(egfr[pick["seqn"]]),
            "acr_first_mg_g": round(pick["acr"]),
            "acr_second_mg_g": round(pick["acr2"]),
            "second_sample_confirms": pick["acr2"] >= 30,
            "engine_rule": order["regla"],
            "engine_order": order["pedido"],
            "engine_review_date": order.get("fecha_revision"),
            "in_baseline_eGFR_lt_60": pick["seqn"] in base,
        }

    out = {
        "data": "NHANES 2009-2010 public-use files (CDC/NCHS), one visit per participant",
        "steps_on_real_data": {
            "1_extract_loaded_participants": len(people),
            "2_rules_fired": {k: fired.get(k, 0) for k in RULES},
            "3_note_reader": "not run: NHANES has no clinical notes",
            "4_S1c": fired.get("S1c", 0),
            "4_rows_removed_from_list_any_reason": removed,
            "extract_rows": tables,
            "s1b_on_one_visit_means": "ACR >= 30 mg/g with no CKD code (dates are fixed by the mapping, not real)",
            "5_orders_prepared": len(result["pedidos"]),
            "orders_with_note_text": notes_read,
        },
        "selection_rule": "diabetes + hypertension, S1b order, second sample; first ACR nearest the group median; ties lowest SEQN",
        "trace": {
            "any_egfr": traced(lambda r: True),
            "egfr_60_or_more": traced(lambda r: egfr[r["seqn"]] >= 60),
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    s = out["steps_on_real_data"]
    md = [
        "# Workflow steps on real data (NHANES 2009-2010)", "",
        "Generated by `python3 eval/nhanes/trace.py`. Descriptive; protocol amendment 8.", "",
        "| Step | On real data |", "|---|---|",
        f"| 1 Extract | {s['1_extract_loaded_participants']:,} participants loaded (one visit each) |",
        "| 2 Signed rules | " + ", ".join(f"{k} {v}" for k, v in s["2_rules_fired"].items() if k != "S1c") + " |",
        f"| 3 Note reader | {s['3_note_reader']} |",
        f"| 4 Final rules | S1c {s['4_S1c']}; removed from the list for any reason {s['4_rows_removed_from_list_any_reason']} (no pending orders in NHANES) |",
        "| Extract contents | " + ", ".join(f"{k} {v}" for k, v in s["extract_rows"].items()) + " rows |",
        f"| Note | {s['s1b_on_one_visit_means']} |",
        f"| 5 Doctor's screen | {s['5_orders_prepared']} orders prepared |", "",
        "## Real participants traced", "",
        f"Selection rule: {out['selection_rule']}.", "",
    ]
    for key, title in (("egfr_60_or_more", "eGFR >= 60 (the diagram's case)"), ("any_egfr", "any eGFR (first rule, first run)")):
        t = out["trace"][key]
        md += [
            f"**{title}** (group of {t['group_size']}, median first ACR {t['group_median_first_acr_mg_g']} mg/g)", "",
            f"- {t['sex'].capitalize()}, age {t['age_band']}, diabetes and hypertension, eGFR {t['egfr']}"
            f" ({'below' if t['in_baseline_eGFR_lt_60'] else 'not below'} 60: a blood-test-only filter {'flags' if t['in_baseline_eGFR_lt_60'] else 'passes'} them).",
            f"- First urine ACR {t['acr_first_mg_g']} mg/g -> engine rule {t['engine_rule']}: \"{t['engine_order']}\".",
            f"- Second urine (within 10 days): ACR {t['acr_second_mg_g']} mg/g -> {'confirmed' if t['second_sample_confirms'] else 'not confirmed'}.",
            "",
        ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
