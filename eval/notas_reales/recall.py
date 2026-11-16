"""Reader recall on the held-out real texts (docs/NOTES_REAL_PROTOCOL.md, amendment 5; round 13, E1).

    python3 eval/notas_reales/recall.py   ->  eval/results/notas_reales_recall.json and .md

Reference: eval/notas_reales/recall_labels_heldout.csv, marked by AI agents that read the numbered case texts
without seeing the model's output or the checks. Not a physician; Ahmed's check of 20 marks is pending.
Primary (pre-registered): per note, the share of notes with at least one marked item in which the code accepted a
finding with the same label on a marked sentence. Also: the share the model pointed to (before the checks).
"""
from __future__ import annotations

import collections
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "notas_reales"))

from notas.leer import LectorGrabado, nota_numerada  # noqa: E402
from notas.verificar import verificar  # noqa: E402
from revisar import HOY, NOTE_DATE, clopper_pearson  # noqa: E402

HERE = ROOT / "eval" / "notas_reales"
LABELS = HERE / "recall_labels_heldout.csv"
OUT = ROOT / "eval" / "results" / "notas_reales_recall"
SEED_CHECK = 20261119


def main() -> int:
    muestra = json.loads((HERE / "muestra_heldout.json").read_text(encoding="utf-8"))
    ids = {c["id"] for c in muestra["cases"]}
    with LABELS.open(encoding="utf-8", newline="") as fh:
        marks = list(csv.DictReader(fh))
    lector = LectorGrabado(HERE / "salidas_heldout_qwen3-4b-instruct-2507.jsonl")
    by_case = collections.defaultdict(list)
    for m in marks:
        if m["case"] not in ids:
            raise SystemExit(f"label for a case outside the held-out sample: {m['case']}")
        by_case[m["case"]].append(m)
    per_note = collections.Counter()
    per_label = collections.defaultdict(collections.Counter)
    strict = collections.Counter()
    misses = []
    for cid, ms in sorted(by_case.items()):
        text = (HERE / "raw" / f"{cid}.txt").read_text(encoding="utf-8")
        n_sent = nota_numerada(text).count("\n[")
        if any(int(m["sentence"]) > n_sent for m in ms):
            raise SystemExit(f"{cid}: a marked sentence is beyond the {n_sent} sentences the reader saw")
        out = lector(text) or {}
        frase, label = out.get("frase"), out.get("etiqueta")
        accepted = [r for r in verificar(text, NOTE_DATE, out, HOY) if r["verificada"] == 1]
        marked = {(m["label"], int(m["sentence"])) for m in ms}
        pointed = (label, frase) in marked
        hit = pointed and any(r["etiqueta"] == label for r in accepted)
        per_note["notes"] += 1
        per_note["pointed"] += pointed
        per_note["accepted"] += hit
        clear = [m for m in ms if "vague" not in (m.get("note") or "").lower()]
        if clear:
            strict["notes"] += 1
            strict["accepted"] += hit and (label, frase) in {(m["label"], int(m["sentence"])) for m in clear}
        for lab in {m["label"] for m in ms}:
            per_label[lab]["notes"] += 1
            per_label[lab]["accepted"] += hit and label == lab
        if not hit:
            misses.append({"case": cid, "model_said": label, "model_sentence": frase,
                           "marked": sorted(f"{a}#{b}" for a, b in marked)})

    def rate(k, n):
        lo, hi = clopper_pearson(k, n)
        return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": [round(100 * lo, 1), round(100 * hi, 1)]}

    rng = random.Random(SEED_CHECK)
    check = rng.sample(sorted(marks, key=lambda m: (m["case"], int(m["sentence"]), m["label"])), 20)
    res = {
        "reference": "AI agents (Claude Sonnet 5.5 sub-agents) blind to the model output; not a physician",
        "physician_check": "pending: Ahmed checks 20 random marks (seed 20261119), listed in physician_check_marks",
        "checks_used": "notas/verificar.py as of round 13 (signed 16 Nov 2026)",
        "cases_in_sample": len(ids),
        "cases_with_a_mark": len(by_case),
        "marks": len(marks),
        "marks_by_label": dict(collections.Counter(m["label"] for m in marks)),
        "marks_by_test": dict(collections.Counter(m["prueba"] or "-" for m in marks)),
        "primary_recall_per_note": rate(per_note["accepted"], per_note["notes"]),
        "model_pointed_per_note": rate(per_note["pointed"], per_note["notes"]),
        "recall_per_note_without_vague_marks": rate(strict["accepted"], strict["notes"]),
        "recall_by_label": {k: rate(v["accepted"], v["notes"]) for k, v in sorted(per_label.items())},
        "missed_notes": misses,
        "physician_check_marks": [{k: m[k] for k in ("case", "sentence", "label", "prueba", "quote")} for m in check],
        "deviation": "one labelling agent (part 2, 100 cases) searched its file for kidney terms instead of reading every sentence",
    }
    OUT.with_suffix(".json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    P = res["primary_recall_per_note"]
    md = ["# Note reader recall on held-out real texts (CodiEsp)", "",
          "Generated by `python3 eval/notas_reales/recall.py` (notes protocol amendment 5). Reference: marks by AI "
          "agents blind to the model's output, **not a physician**; Ahmed's check of 20 marks is pending.", "",
          f"- Cases with at least one marked finding: {res['cases_with_a_mark']} of {res['cases_in_sample']} "
          f"({res['marks']} marks: {res['marks_by_label']}; tests {res['marks_by_test']}).",
          f"- **Recall per note (primary): {P['k']} of {P['n']}, {P['pct']} % (95 % CI {P['ci95'][0]}–{P['ci95'][1]}).**",
          f"- The model pointed to a marked sentence in {res['model_pointed_per_note']['k']} of {P['n']} notes.",
          f"- Without the {sum(1 for m in marks if 'vague' in (m.get('note') or '').lower())} marks the labeller "
          f"called vague (not pre-registered): {res['recall_per_note_without_vague_marks']['k']} of {res['recall_per_note_without_vague_marks']['n']}.",
          "- By label: " + "; ".join(f"{k} {v['k']} of {v['n']}" for k, v in res["recall_by_label"].items()) + ".", "",
          "**What it means.** These are hospital case reports, where almost every case lists a creatinine value. The "
          "reader was built to find a test reported in a primary-care note (\"trae analítica de la mutua: FGe 63\"), "
          "and returns one finding per note. Missing a creatinine value in a hospital report is a miss by the "
          "definition, but it does not change an order here: a note never removes an eGFR order (round 13, R5). "
          "No CAC finding existed in this sample, so recall for the findings that can remove an order is not measured.",
          "", f"Deviation: {res['deviation']}.", ""]
    OUT.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
