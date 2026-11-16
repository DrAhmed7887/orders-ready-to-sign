"""Run the unmodified engine on NHANES and write the pre-registered measures (docs/EVAL_PROTOCOL.md).

    python3 eval/nhanes/fetch.py && python3 eval/nhanes/run.py
    → eval/results/nhanes.json and eval/results/nhanes.md

Deterministic: no random step, no model call, no key. Needs pandas (+ scipy for exact t quantiles): requirements-eval.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from core import (Participant, baseline_ids, extract_sql, flags_from_engine,  # noqa: E402
                  in_population, survey_proportion)
from ejecutar import construir, generar  # noqa: E402

try:
    import scipy  # noqa: F401  (exact t quantiles; the CIs in the committed results depend on it)
except ImportError:  # pragma: no cover
    sys.exit("scipy is required: pip install -r requirements-eval.txt")

RAW = HERE / "raw"
OUT_JSON = ROOT / "eval" / "results" / "nhanes.json"
OUT_MD = ROOT / "eval" / "results" / "nhanes.md"
CDC_NOTE = ("CDC/NCHS, NHANES 2009-2010 ALB_CR_F codebook, analytic note (read 15 Nov 2026): adults >=20 y (n=5247), "
            "weighted mean ACR 23.7 mg/g (random urine, first collection) and 15.9 mg/g (first-morning void, second "
            "collection); ACR >=30 mg/g in 7.7 % and 3.4 %, MEC weights.")


def _load(names: List[str]):
    import pandas as pd
    frames = [pd.read_sas(RAW / f"{n}.xpt", format="xport") for n in names]
    df = frames[0]
    for f in frames[1:]:
        df = df.merge(f, on="SEQN", how="left")
    return df


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f   # NaN -> None


def _participants(df, with_acr2: bool) -> Dict[int, dict]:
    """Every examined participant (weight > 0), with the protocol's population flag."""
    out = {}
    for r in df.itertuples(index=False):
        w = _num(getattr(r, "WTMEC2YR"))
        if not w or w <= 0:
            continue
        age, scr, acr = _num(r.RIDAGEYR), _num(r.LBXSCR), _num(r.URDACT)
        preg = _num(getattr(r, "RIDEXPRG", None)) == 1
        dm, htn = _num(r.DIQ010) == 1, _num(r.BPQ020) == 1
        rec = {"seqn": int(r.SEQN), "age": age, "female": _num(r.RIAGENDR) == 2, "dm": dm, "htn": htn,
               "scr": scr, "acr": acr, "acr2": _num(getattr(r, "URDACT2", None)) if with_acr2 else None,
               "w": w, "h": int(r.SDMVSTRA), "j": int(r.SDMVPSU), "preg": preg}
        rec["pop"] = in_population(age, preg, dm, htn, scr, acr, w)
        out[rec["seqn"]] = rec
    return out


def _engine(recs: Dict[int, dict], source: str):
    people = [Participant(r["seqn"], r["age"], r["female"], r["dm"], r["htn"], r["scr"], r["acr"], r["w"], r["h"], r["j"])
              for r in recs.values() if r["pop"]]
    egfr = {p.seqn: p.egfr for p in people}
    result = generar(construir(extract_sql(people, source)))
    return people, egfr, flags_from_engine(result), set(baseline_ids(result)), result


def _est(recs, y_fn, d_fn):
    rs = list(recs.values())
    return survey_proportion([int(bool(y_fn(r))) for r in rs], [int(bool(d_fn(r))) for r in rs],
                             [r["w"] for r in rs], [r["h"] for r in rs], [r["j"] for r in rs]).per_1000()


def primary() -> dict:
    recs = _participants(_load(["DEMO_L", "BIOPRO_L", "ALB_CR_L", "DIQ_L", "BPQ_L"]), with_acr2=False)
    people, egfr, flags, base, result = _engine(recs, "nhanes_2021_2023")
    for r in recs.values():
        r["egfr"] = egfr.get(r["seqn"])
        r["flag"] = r["seqn"] in flags
        r["base"] = r["seqn"] in base
    pop = lambda r: r["pop"]  # noqa: E731
    alb = lambda r: r["acr"] is not None and r["acr"] >= 30  # noqa: E731
    low = lambda r: r["egfr"] is not None and r["egfr"] < 60  # noqa: E731
    hidden = lambda r: pop(r) and alb(r) and not low(r)  # noqa: E731
    marker = lambda r: pop(r) and (alb(r) or low(r))  # noqa: E731
    # End-to-end check: on one visit, the engine should flag exactly ACR >= 30 (S1b). List every exception.
    mismatches = [{"seqn": r["seqn"], "acr": r["acr"], "egfr": round(r["egfr"], 1), "engine_rule": flags.get(r["seqn"])}
                  for r in recs.values() if pop(r) and alb(r) != r["flag"]]
    exclusions = {
        "examined_adults": sum(1 for r in recs.values() if r["age"] is not None and r["age"] >= 18),
        "with_diabetes_or_hypertension": sum(1 for r in recs.values() if (r["age"] or 0) >= 18 and (r["dm"] or r["htn"])),
        "pregnant_excluded": sum(1 for r in recs.values() if (r["age"] or 0) >= 18 and (r["dm"] or r["htn"]) and r["preg"]),
        "missing_creatinine_or_acr": sum(1 for r in recs.values() if (r["age"] or 0) >= 18 and (r["dm"] or r["htn"])
                                         and not r["preg"] and (r["scr"] is None or r["acr"] is None)),
        "in_population": len(people),
    }
    return {
        "cycle": "NHANES August 2021-August 2023",
        "population": exclusions,
        "engine_rules_fired": {k: sum(1 for v in flags.values() if v == k) for k in sorted(set(flags.values()))},
        "per_1000_adults_with_diabetes_or_hypertension": {
            "albuminuria_behind_acceptable_egfr (ACR>=30, eGFR>=60; missed by baseline)": _est(recs, hidden, pop),
            "of_those_flagged_by_engine (per 1000 hidden; same threshold, so 1000 by construction)": _est(recs, lambda r: r["flag"], hidden),
            "baseline_flags (eGFR<60)": _est(recs, lambda r: r["base"], pop),
            "engine_flags": _est(recs, lambda r: r["flag"], pop),
            "kidney_marker (eGFR<60 or ACR>=30, single visit)": _est(recs, marker, pop),
        },
        "share_of_kidney_markers_found (per 1000 with a marker)": {
            "baseline_eGFR<60_only": _est(recs, lambda r: r["base"], marker),
            "engine_only (= ACR>=30 on one visit)": _est(recs, lambda r: r["flag"], marker),
        },
        "by_construction": "baseline + engine together find every single-visit marker (1000 per 1000): the marker is "
                           "defined as eGFR<60 or ACR>=30, which is exactly the union of the two. Not a result.",
        "end_to_end_check": {"engine_flag_differs_from_ACR>=30": len(mismatches), "examples": mismatches[:20]},
        "note": "On one visit the engine's S1b threshold and the albuminuria reference are the same: "
                "'engine flags' checks the pipeline on real values, it is not an accuracy claim.",
    }


def secondary() -> dict:
    recs = _participants(_load(["DEMO_F", "BIOPRO_F", "ALB_CR_F", "DIQ_F", "BPQ_F"]), with_acr2=True)
    people, egfr, flags, base, _ = _engine(recs, "nhanes_2009_2010")
    for r in recs.values():
        r["flag"] = r["seqn"] in flags
    has2 = lambda r: r["pop"] and r["acr2"] is not None  # noqa: E731
    conf = lambda r: r["acr2"] is not None and r["acr2"] >= 30  # noqa: E731
    adult20 = lambda r: r["age"] is not None and r["age"] >= 20  # noqa: E731
    return {
        "cycle": "NHANES 2009-2010 (second urine = first-morning void at home within 10 days)",
        "population_with_second_sample": sum(1 for r in recs.values() if has2(r)),
        "population_without_second_sample": sum(1 for r in recs.values() if r["pop"] and r["acr2"] is None),
        "repeat_orders_confirmed (per 1000 engine 'repeat ACR' orders, second ACR>=30)":
            _est(recs, conf, lambda r: has2(r) and r["flag"]),
        "missed_by_single_test (per 1000 not flagged, second ACR>=30)":
            _est(recs, conf, lambda r: has2(r) and not r["flag"]),
        "published_check": _published_check(recs),
    }


def _wmean(rs, key):
    return sum(r["w"] * r[key] for r in rs) / sum(r["w"] for r in rs)


def _wmedian(rs, key):
    """Weighted median: the first value where the cumulative weight reaches half the total."""
    pairs = sorted((r[key], r["w"]) for r in rs)
    half, acc = sum(w for _, w in pairs) / 2, 0.0
    for v, w in pairs:
        acc += w
        if acc >= half:
            return v
    return pairs[-1][0]


def _published_check(recs) -> dict:
    """CDC's analytic note uses adults >= 20 with BOTH urine samples (n = 5247), MEC weights, point estimates only."""
    both = [r for r in recs.values() if r["age"] is not None and r["age"] >= 20
            and r["acr"] is not None and r["acr2"] is not None]
    sw = sum(r["w"] for r in both)
    pct = lambda cond: round(100 * sum(r["w"] for r in both if cond(r)) / sw, 1)  # noqa: E731
    rows = {
        "n": (len(both), 5247),
        "mean_acr_first_mg_g": (round(_wmean(both, "acr"), 1), 23.7),
        "mean_acr_second_mg_g": (round(_wmean(both, "acr2"), 1), 15.9),
        "median_acr_first_mg_g": (round(_wmedian(both, "acr"), 1), 6.0),
        "median_acr_second_mg_g": (round(_wmedian(both, "acr2"), 1), 4.5),
        "acr_ge_30_first_pct": (pct(lambda r: r["acr"] >= 30), 7.7),
        "acr_ge_30_second_pct (as the note words it)": (pct(lambda r: r["acr2"] >= 30), 3.4),
        "acr_ge_30_on_both_pct (alternative reading)": (pct(lambda r: r["acr"] >= 30 and r["acr2"] >= 30), 3.4),
    }
    out = {"source": CDC_NOTE}
    for k, (ours, pub) in rows.items():
        out[k] = {"ours": ours, "published": pub, "matches": round(float(ours), 1) == pub}
    out["reading"] = ("All figures match except 'ACR >= 30 on the second collection' (ours 4.7 % vs 3.4 %). "
                      "The CDC's 3.4 % matches ACR >= 30 on BOTH samples (persistent), so the note most likely "
                      "reports persistence under the label 'second collection'. Unconfirmed with CDC.")
    return out


def to_md(res: dict) -> str:
    lines = ["# NHANES external evaluation (pre-registered: docs/EVAL_PROTOCOL.md)", "",
             "Generated by `python3 eval/nhanes/run.py`. Survey-weighted (MEC weights, strata, PSU), 95 % CI.", ""]

    def table(title, d):
        lines.extend([f"## {title}", "", "| Measure | Per 1,000 | 95 % CI | n (events) |", "|---|---|---|---|"])
        for k, v in d.items():
            lines.append(f"| {k} | {v['per_1000']} | {v['ci95_lo']}–{v['ci95_hi']} | {v['n']} ({v['events']}) |")
        lines.append("")
    p, s = res["primary"], res["secondary"]
    lines.append(f"**{p['cycle']}** · population: `{json.dumps(p['population'])}` · rules fired: `{json.dumps(p['engine_rules_fired'])}`")
    lines.append("")
    table("Primary: per 1,000 adults with diabetes or hypertension", p["per_1000_adults_with_diabetes_or_hypertension"])
    table("Who finds the kidney markers", p["share_of_kidney_markers_found (per 1000 with a marker)"])
    lines.append(f"By construction: {p['by_construction']}")
    lines.append("")
    lines.append(f"End-to-end check: engine flag differs from ACR ≥ 30 in **{p['end_to_end_check']['engine_flag_differs_from_ACR>=30']}** participants. {p['note']}")
    lines.append("")
    lines.append(f"**{s['cycle']}** · with a second sample: {s['population_with_second_sample']}, without: {s['population_without_second_sample']}")
    lines.append("")
    table("Secondary: does the 'repeat ACR' order confirm?", {k: v for k, v in s.items() if isinstance(v, dict) and "per_1000" in v})
    pc = s["published_check"]
    lines.extend(["## Check against a published figure", "", f"Source: {pc['source']}", "",
                  "| Figure | Ours | Published | Matches |", "|---|---|---|---|"])
    for k, v in pc.items():
        if isinstance(v, dict):
            lines.append(f"| {k} | {v['ours']} | {v['published']} | {'yes' if v['matches'] else '**no**'} |")
    lines.extend(["", f"**Reading:** {pc['reading']}", ""])
    return "\n".join(lines)


def main() -> int:
    missing = [n for n in ("DEMO_L", "ALB_CR_F") if not (RAW / f"{n}.xpt").exists()]
    if missing:
        print("raw files missing: run python3 eval/nhanes/fetch.py first", file=sys.stderr)
        return 1
    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    res = {"protocol": "docs/EVAL_PROTOCOL.md", "files": {k: v["sha256"] for k, v in manifest.items()},
           "primary": primary(), "secondary": secondary()}
    OUT_JSON.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    OUT_MD.write_text(to_md(res))
    print(OUT_MD.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
