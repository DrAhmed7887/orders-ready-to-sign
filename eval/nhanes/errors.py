"""Error table for the engine's repeat-ACR orders on real data (protocol amendment 9, descriptive).

    python3 eval/nhanes/errors.py   ->  eval/results/nhanes_errors.json and .md

Why: published sepsis-alert evaluations report error at the operating point, not one headline number.
- Sensitivity, misses and alert burden: Wong et al., JAMA Intern Med 2021, doi:10.1001/jamainternmed.2021.2626.
- Added value over usual care: same study.
- Held-out sites: Reyna et al., Crit Care Med 2020, doi:10.1097/CCM.0000000000004145.

Data: NHANES 2009-2010, the only cycle with a second urine ACR (a first-morning void within 10 days). Population:
the protocol population (adults with diagnosed diabetes or hypertension, both labs, not pregnant) with a second
sample. Reference standard: ACR >= 30 mg/g on the SECOND sample, which the rules never see. This is a 10-day
repeat, not KDIGO's 3-month persistence, so the reference is itself imperfect.

Strategies compared, each run on the same one-visit extracts:
  engine    = an S1b repeat-ACR order (ACR >= 30 on the first sample, no CKD code)
  baseline  = last eGFR < 60 (a blood-test-only filter)
  combined  = either one (what a list would see if the engine runs alongside the blood-test filter)
All estimates are survey-weighted (MEC weights, strata, PSUs; Taylor linearisation, logit CI), as in run.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "nhanes"))

OUT_JSON = ROOT / "eval" / "results" / "nhanes_errors.json"
OUT_MD = ROOT / "eval" / "results" / "nhanes_errors.md"


def main() -> int:
    from run import _engine, _est, _load, _participants  # needs scipy (requirements-eval.txt)

    recs = _participants(_load(["DEMO_F", "BIOPRO_F", "ALB_CR_F", "DIQ_F", "BPQ_F"]), with_acr2=True)
    _, _, flags, base, _ = _engine(recs, "nhanes_2009_2010")
    other = {v for v in flags.values() if v != "S1b"}
    if other:
        raise SystemExit(f"rules other than S1b fired on one-visit data: {sorted(other)}")
    for r in recs.values():
        r["engine"] = flags.get(r["seqn"]) == "S1b"
        r["baseline"] = r["seqn"] in base
        r["combined"] = r["engine"] or r["baseline"]
    dom = lambda r: r["pop"] and r["acr2"] is not None  # noqa: E731
    ref = lambda r: r["acr2"] is not None and r["acr2"] >= 30  # noqa: E731

    def table(s):
        fl = lambda r: r[s]  # noqa: E731
        ppv = _est(recs, ref, lambda r: dom(r) and fl(r))
        return {
            "sensitivity": _est(recs, fl, lambda r: dom(r) and ref(r)),
            "specificity": _est(recs, lambda r: not fl(r), lambda r: dom(r) and not ref(r)),
            "ppv": ppv,
            "npv": _est(recs, lambda r: not ref(r), lambda r: dom(r) and not fl(r)),
            "flagged_per_1000": _est(recs, fl, dom),
            "missed_per_1000": _est(recs, lambda r: ref(r) and not fl(r), dom),
            "false_alarms_per_1000": _est(recs, lambda r: fl(r) and not ref(r), dom),
            "number_needed_to_evaluate": {"point": round(1000 / ppv["per_1000"], 2),
                                          "ci95": [round(1000 / ppv["ci95_hi"], 2), round(1000 / ppv["ci95_lo"], 2)]},
            "counts_unweighted": {
                "tp": sum(1 for r in recs.values() if dom(r) and fl(r) and ref(r)),
                "fp": sum(1 for r in recs.values() if dom(r) and fl(r) and not ref(r)),
                "fn": sum(1 for r in recs.values() if dom(r) and not fl(r) and ref(r)),
                "tn": sum(1 for r in recs.values() if dom(r) and not fl(r) and not ref(r)),
            },
        }

    res = {
        "data": "NHANES 2009-2010; reference = ACR >= 30 mg/g on the second urine (first-morning void within 10 days)",
        "population_with_second_sample": sum(1 for r in recs.values() if dom(r)),
        "reference_positive_unweighted": sum(1 for r in recs.values() if dom(r) and ref(r)),
        "strategies": {s: table(s) for s in ("engine", "baseline", "combined")},
        "added_value_over_baseline": {
            # Like "flagged and not already treated" in the Epic Sepsis Model validation: what the blood-test
            # filter would not have found.
            "reference_positive_missed_by_baseline_per_1000_ref": _est(recs, lambda r: not r["baseline"], lambda r: dom(r) and ref(r)),
            "of_those_found_by_engine_per_1000": _est(recs, lambda r: r["engine"], lambda r: dom(r) and ref(r) and not r["baseline"]),
            "found_only_by_engine_per_1000_population": _est(recs, lambda r: ref(r) and r["engine"] and not r["baseline"], dom),
        },
        "nonresponse_sensitivity": _nonresponse(recs, _est, dom, ref),
        "not_measured": [
            "discrimination: the engine's flag (ACR >= 30 on the first sample) and the reference (ACR >= 30 on the "
            "second) are the same test, so sensitivity and specificity are largely 10-day test-retest agreement; "
            "the eGFR filter was never meant to detect albuminuria",
            "persistence over 3 months (KDIGO): the second sample is within 10 days",
            "calibration: the rules give no scores, only orders",
            "other countries or record systems: US survey data only (cf. Reyna 2020 on generalisability)",
            "outcomes after a signed order (cf. Adams 2022, TREWS): no prospective study",
            "note reader recall",
        ],
    }
    OUT_JSON.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    md = render_md(res)
    OUT_MD.write_text(md, encoding="utf-8")
    print(md)
    return 0


def _nonresponse(recs, _est, dom, ref):
    """Round 13, E3 (descriptive): people without a second sample had a high first ACR more often. Re-weight the
    respondents by the inverse of the weighted response rate in cells of first-ACR band (<30, 30-44, 45-99, 100-299,
    >=300 mg/g) x age (18-39 / 40-59 / 60+) x diabetes, then recompute the engine's PPV, sensitivity and misses.
    The first-ACR band matters because confirmation rises steeply with it, so a band shift among non-responders
    could move the PPV; a single ">= 30" cell could not. Sensitivity analysis only; primary figures unchanged."""
    def band(a):
        return None if a is None else 0 if a < 30 else 1 if a < 45 else 2 if a < 100 else 3 if a < 300 else 4

    cell = lambda r: (band(r["acr"]), 0 if r["age"] < 40 else 1 if r["age"] < 60 else 2, bool(r["dm"]))  # noqa: E731
    elig = [r for r in recs.values() if r["pop"]]
    tot, resp = {}, {}
    for r in elig:
        c = cell(r)
        tot[c] = tot.get(c, 0) + r["w"]
        resp[c] = resp.get(c, 0) + (r["w"] if r["acr2"] is not None else 0)
    rate = {c: resp[c] / tot[c] for c in tot if resp[c] > 0}
    adj = {k: dict(r) for k, r in recs.items()}
    for r in adj.values():
        if r["pop"] and r["acr2"] is not None:
            r["w"] = r["w"] / rate[cell(r)]
    no2 = [r for r in elig if r["acr2"] is None]
    yes2 = [r for r in elig if r["acr2"] is not None]
    hi = lambda rs: round(100 * sum(1 for r in rs if r["acr"] is not None and r["acr"] >= 30) / max(1, len(rs)), 1)  # noqa: E731
    return {"first_acr_ge_30_without_second_sample_pct_unweighted": hi(no2),
            "first_acr_ge_30_with_second_sample_pct_unweighted": hi(yes2),
            "cells": "first-ACR band (<30, 30-44, 45-99, 100-299, >=300) x age 18-39/40-59/60+ x diabetes",
            "engine_ppv_reweighted": _est(adj, ref, lambda r: dom(r) and r["engine"]),
            "engine_sensitivity_reweighted": _est(adj, lambda r: r["engine"], lambda r: dom(r) and ref(r)),
            "engine_missed_per_1000_reweighted": _est(adj, lambda r: ref(r) and not r["engine"], dom)}


def render_md(res: dict) -> str:
    def f(e):
        return f"{e['per_1000'] / 10:.1f} % ({e['ci95_lo'] / 10:.1f}–{e['ci95_hi'] / 10:.1f})"

    def k(e):
        return f"{e['per_1000']:.1f} ({e['ci95_lo']:.1f}–{e['ci95_hi']:.1f})"

    md = ["# Error table: repeat-ACR orders on real data (NHANES 2009-2010)", "",
          "Generated by `python3 eval/nhanes/errors.py` (amendment 9, descriptive). Reference: ACR ≥ 30 mg/g on the "
          f"second urine (within 10 days), which the rules never see. Population with a second sample: "
          f"{res['population_with_second_sample']:,} (reference-positive: {res['reference_positive_unweighted']}). "
          "Survey-weighted, 95 % CI.", "",
          "| | Engine (S1b order) | Blood-test filter (eGFR < 60) | Both together |", "|---|---|---|---|"]
    S = res["strategies"]
    rows = [("Sensitivity", "sensitivity", f), ("Specificity", "specificity", f), ("PPV (order confirmed)", "ppv", f),
            ("NPV", "npv", f), ("Flagged per 1,000", "flagged_per_1000", k), ("Missed per 1,000", "missed_per_1000", k),
            ("False alarms per 1,000", "false_alarms_per_1000", k)]
    for label, key, fmt in rows:
        md.append(f"| {label} | " + " | ".join(fmt(S[s][key]) for s in ("engine", "baseline", "combined")) + " |")
    md.append("| Number needed to evaluate (orders per confirmed case) | " + " | ".join(
        f"{S[s]['number_needed_to_evaluate']['point']:.2f} ({S[s]['number_needed_to_evaluate']['ci95'][0]:.2f}–{S[s]['number_needed_to_evaluate']['ci95'][1]:.2f})"
        for s in ("engine", "baseline", "combined")) + " |")
    md.append("| Counts (TP / FP / FN / TN, unweighted) | " + " | ".join(
        "{tp} / {fp} / {fn} / {tn}".format(**S[s]["counts_unweighted"]) for s in ("engine", "baseline", "combined")) + " |")
    A = res["added_value_over_baseline"]
    md += ["", "## What the engine adds to the blood-test filter", "",
           f"- Of people whose second sample is high, the blood-test filter misses {f(A['reference_positive_missed_by_baseline_per_1000_ref'])}.",
           f"- Of those, the engine orders a repeat for {f(A['of_those_found_by_engine_per_1000'])}.",
           "- Missed per 1,000 people on the list is not the same as the earlier \"13.5 per 1,000 not flagged\" "
           "(1 − NPV): same 28 people, different denominator.",
           f"- Found only by the engine: {k(A['found_only_by_engine_per_1000_population'])} per 1,000 people on the list.", "",
           "## Non-response check (round 13, E3, descriptive)", "",
           f"- High first ACR: {res['nonresponse_sensitivity']['first_acr_ge_30_without_second_sample_pct_unweighted']} % of people "
           f"without a second sample vs {res['nonresponse_sensitivity']['first_acr_ge_30_with_second_sample_pct_unweighted']} % with one (unweighted).",
           f"- Engine PPV after re-weighting respondents ({res['nonresponse_sensitivity']['cells']}): "
           f"PPV {f(res['nonresponse_sensitivity']['engine_ppv_reweighted'])}, sensitivity "
           f"{f(res['nonresponse_sensitivity']['engine_sensitivity_reweighted'])}, missed "
           f"{k(res['nonresponse_sensitivity']['engine_missed_per_1000_reweighted'])} per 1,000.", "",
           "## Not measured", "", *[f"- {x}" for x in res["not_measured"]], ""]
    return "\n".join(md)


if __name__ == "__main__":
    raise SystemExit(main())
