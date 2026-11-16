"""Replay the recorded model outputs on the real sample, run the unchanged checks, and build Ahmed's review sheet.

    python3 eval/notas_reales/revisar.py
      -> eval/results/notas_reales.json / .md     what the model said and what the code accepted or rejected
      -> eval/notas_reales/hoja_revision.html      one card per ACCEPTED finding, for the physician to mark
    python3 eval/notas_reales/revisar.py --puntuar <review.csv> --revisor "<who>"
      -> adds the primary measure (wrong accepted findings per 100 notes, exact 95 % CI) to the results

Protocol: docs/NOTES_REAL_PROTOCOL.md (amendment 1). No model is called here; CI can replay it.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from notas.leer import LectorGrabado, MAX_CARACTERES  # noqa: E402
from notas.verificar import frases, normalizar, verificar  # noqa: E402

HERE = ROOT / "eval" / "notas_reales"
MUESTRA = HERE / "muestra.json"
GRABADAS = HERE / "salidas_qwen3-4b-instruct-2507.jsonl"
OUT_JSON = ROOT / "eval" / "results" / "notas_reales.json"
OUT_MD = ROOT / "eval" / "results" / "notas_reales.md"
HOJA = HERE / "hoja_revision.html"
NOTE_DATE = HOY = "2026-06-01"   # case reports have no visit date: fixed placeholder (protocol)
VERDICTS = ["correct", "not_this_patient", "not_a_result", "wrong_value_or_unit", "wrong_label", "other"]


def could_change(a) -> bool:
    """Only a dated "test done" finding can remove an order or (with a value) confirm albuminuria."""
    return a["label"] == "ya_realizada" and a["date"] is not None


def clopper_pearson(k: int, n: int):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(0.025, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(0.975, k + 1, n - k)
    return lo, hi


CONJUNTOS = {   # name -> (sample, recording, results base, review sheet)
    "dev": (MUESTRA, GRABADAS, ROOT / "eval/results/notas_reales", HOJA),
    "heldout": (HERE / "muestra_heldout.json", HERE / "salidas_heldout_qwen3-4b-instruct-2507.jsonl",
                ROOT / "eval/results/notas_reales_heldout", HERE / "hoja_revision_heldout.html"),
    "heldout2": (HERE / "muestra_heldout2.json", HERE / "salidas_heldout2_qwen3-4b-instruct-2507.jsonl",
                 ROOT / "eval/results/notas_reales_heldout2", HERE / "hoja_revision_heldout2.html"),
}


def analyse(conjunto: str = "dev"):
    muestra_p, grabadas_p, _, _ = CONJUNTOS[conjunto]
    muestra = json.loads(muestra_p.read_text(encoding="utf-8"))
    lector = LectorGrabado(grabadas_p)
    said = collections.Counter()
    said_by_stratum = collections.defaultdict(collections.Counter)
    rejected = collections.Counter()
    accepted = []
    for c in muestra["cases"]:
        text = (HERE / "raw" / f"{c['id']}.txt").read_text(encoding="utf-8")
        salida = lector(text)
        etiqueta = ("no output" if salida is None else
                    salida.get("etiqueta", "malformed") if isinstance(salida, dict) else "malformed")
        said[etiqueta] += 1
        said_by_stratum[c["stratum"]][etiqueta] += 1
        sents = frases(normalizar(text))
        for i, row in enumerate(verificar(text, NOTE_DATE, salida, HOY)):
            if row["verificada"] == 1:
                k = (salida or {}).get("frase")
                k = k if isinstance(k, int) else None
                accepted.append({
                    "key": f"{c['id']}#{i}", "case": c["id"], "stratum": c["stratum"], "label": row["etiqueta"],
                    "test": row.get("prueba"), "value": row.get("valor"), "unit": row.get("unidad"),
                    "date": row.get("fecha_cita"), "note": row.get("motivo_rechazo"), "sentence_no": k,
                    "sentence": row.get("cita"),
                    "before": sents[k - 2] if k and k >= 2 else "",
                    "after": sents[k] if k and k < len(sents) else "",
                })
            elif row.get("motivo_rechazo"):
                rejected[row["motivo_rechazo"]] += 1
    long_cut = sum(1 for c in muestra["cases"]
                   if len((HERE / "raw" / f"{c['id']}.txt").read_text(encoding="utf-8")) > MAX_CARACTERES)
    analyse.by_stratum = {k: dict(v) for k, v in sorted(said_by_stratum.items())}
    return muestra, lector, said, rejected, accepted, long_cut


LIVINGNER = ("LivingNER v6.3.1, Miranda-Escalada, Farré-Maduell, Lima-López, González Gacio, Krallinger, "
             "doi:10.5281/zenodo.7684093")
CODIESP = "CodiEsp v1.4, Miranda-Escalada, Gonzalez-Agirre, Armengol-Estapé,\nKrallinger, doi:10.5281/zenodo.3837305"


def sheet(accepted, fuente=CODIESP):
    data = json.dumps(accepted, ensure_ascii=False).replace("<", "\\u003c")
    verdicts = json.dumps(VERDICTS)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review accepted findings</title>
<style>
:root{{--bg:#f5f6f8;--panel:#fff;--ink:#0e1726;--muted:#5d6779;--line:#e4e7ec;--accent:#0b6b61;--soft:#e6f2f0;--bad:#b42318}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f141b;--panel:#171e27;--ink:#eef2f6;--muted:#9aa6b5;--line:#2a3441;--accent:#3fb8a8;--soft:#12302c;--bad:#f97066}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Inter,system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:860px;margin:0 auto;padding:16px}}
header{{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);z-index:1}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0}}
.card.done{{border-color:var(--accent)}} .card.bad{{border-color:var(--bad)}}
.meta{{color:var(--muted);font-size:14px}} .ctx{{color:var(--muted)}}
.s{{background:var(--soft);padding:2px 4px;border-radius:4px}}
.read{{font-weight:600;margin:8px 0}}
label{{display:inline-flex;gap:6px;align-items:center;margin:4px 12px 4px 0;font-size:15px}}
input[type=text]{{width:100%;box-sizing:border-box;padding:6px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink)}}
button{{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}}
</style></head><body><main>
<header><b>Accepted findings on real case reports: is each one right?</b>
<div class="meta">Excerpts (whitespace-normalised) from {fuente}, licence CC BY 4.0 (creativecommons.org/licenses/by/4.0); see NOTICE.md. Mark each card, then Export CSV and
save it as <code>eval/notas_reales/revision_ahmed.csv</code>. Progress is kept in this browser.</div>
<div><span id="prog"></span> &nbsp; <button id="exp">Export CSV</button></div></header>
<div id="list"></div></main>
<script>
const ROWS = {data};
const VERDICTS = {verdicts};
const NAMES = {{correct:"Correct", not_this_patient:"Not about this patient", not_a_result:"Not a result / not done",
  wrong_value_or_unit:"Wrong value or unit", wrong_label:"Wrong label", other:"Other"}};
const KEY = "revision-notas-reales-v1";
let state = {{}};
try {{ state = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{ state = {{}}; }}
const save = () => {{ try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}} render(); }};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}})[c]);
function render() {{
  const n = ROWS.filter((r) => state[r.key]?.verdict).length;
  document.getElementById("prog").textContent = `${{n}} of ${{ROWS.length}} reviewed`;
  document.querySelectorAll(".card").forEach((el) => {{
    const v = state[el.dataset.key]?.verdict;
    el.classList.toggle("done", v === "correct"); el.classList.toggle("bad", !!v && v !== "correct");
  }});
}}
const list = document.getElementById("list");
ROWS.forEach((r, i) => {{
  const el = document.createElement("section");
  el.className = "card"; el.dataset.key = r.key;
  const read = r.label === "ya_realizada"
    ? `Code read: test already done · ${{esc(r.test)}} = ${{esc(r.value ?? "no value")}} ${{esc(r.unit ?? "")}}${{r.date ? " · " + esc(r.date) : " · no date"}}`
    : r.label === "rechazo" ? "Code read: the patient refuses the test" : "Code read: followed in Nephrology";
  el.innerHTML = `<div class="meta">${{i + 1}} / ${{ROWS.length}} · case ${{esc(r.case)}} · sentence ${{esc(r.sentence_no)}}</div>
    <p><span class="ctx">${{esc(r.before)}}</span> <span class="s">${{esc(r.sentence)}}</span> <span class="ctx">${{esc(r.after)}}</span></p>
    <div class="read">${{read}}${{r.note ? " · note: " + esc(r.note) : ""}}</div>
    <div>${{VERDICTS.map((v) => `<label><input type="radio" name="v${{i}}" value="${{v}}">${{NAMES[v]}}</label>`).join("")}}</div>
    <input type="text" placeholder="Comment (optional)">`;
  el.querySelectorAll("input[type=radio]").forEach((b) => {{
    if (state[r.key]?.verdict === b.value) b.checked = true;
    b.addEventListener("change", () => {{ state[r.key] = {{...state[r.key], verdict: b.value}}; save(); }});
  }});
  const c = el.querySelector("input[type=text]");
  c.value = state[r.key]?.comment || "";
  c.addEventListener("input", () => {{ state[r.key] = {{...state[r.key], comment: c.value}}; save(); }});
  list.appendChild(el);
}});
document.getElementById("exp").addEventListener("click", () => {{
  const q = (s) => '"' + String(s ?? "").replace(/"/g, '""') + '"';
  const lines = ["key,verdict,comment", ...ROWS.map((r) => [r.key, state[r.key]?.verdict || "", state[r.key]?.comment || ""].map(q).join(","))];
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([lines.join("\\n") + "\\n"], {{type: "text/csv"}}));
  a.download = "revision_ahmed.csv"; a.click();
}});
render();
</script></body></html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--puntuar", type=Path, help="review CSV (key,verdict,comment)")
    ap.add_argument("--revisor", help="who reviewed; must say whether AI or physician (stated in the results)")
    ap.add_argument("--dudosos", default="", help="comma-separated keys judged 'correct' that are judgment calls")
    ap.add_argument("--conjunto", choices=sorted(CONJUNTOS), default="dev")
    args = ap.parse_args(argv)
    _, _, base, hoja = CONJUNTOS[args.conjunto]
    out_json, out_md = base.with_suffix(".json"), base.with_suffix(".md")
    muestra, lector, said, rejected, accepted, long_cut = analyse(args.conjunto)
    n = len(muestra["cases"])
    res = {
        "source": muestra["source"], "cases": n, "model": lector.modelo,
        "checks_sha256": hashlib.sha256((ROOT / "notas" / "verificar.py").read_bytes()).hexdigest(),
        "missing_outputs": len(lector.sin_grabar), "cases_cut_at_6000_chars": long_cut,
        "model_said": dict(said.most_common()),
        "model_said_by_stratum": analyse.by_stratum,
        "accepted_findings": len(accepted),
        "accepted_by_label": dict(collections.Counter(a["label"] for a in accepted).most_common()),
        "rejected_by_reason": dict(rejected.most_common()),
    }
    if args.puntuar:
        if not args.revisor or not any(w in args.revisor.lower() for w in ("ai ", "agent", "physician")):
            raise SystemExit("--revisor is required and must say whether the reviewer is an AI agent or a physician")
        with args.puntuar.open(encoding="utf-8", newline="") as fh:
            rev = {r["key"]: r for r in csv.DictReader(fh)}
        keys = {a["key"] for a in accepted}
        bad = [k for k, r in rev.items() if k not in keys or r.get("verdict") not in VERDICTS + [""]]
        if bad:
            raise SystemExit(f"review CSV has unknown keys or verdicts: {bad[:3]}")
        missing = [a["key"] for a in accepted if not rev.get(a["key"], {}).get("verdict")]
        if missing:
            raise SystemExit(f"{len(missing)} accepted findings not reviewed, e.g. {missing[:3]}")
        wrong = [a for a in accepted if rev[a["key"]]["verdict"] != "correct"]
        # The interval is per note: count notes with at least one wrong finding (a note can give more than one).
        notes_wrong = len({a["case"] for a in wrong})
        lo, hi = clopper_pearson(notes_wrong, n)
        strata = dict(collections.Counter(c["stratum"] for c in muestra["cases"]).most_common())
        dudosos = [k for k in args.dudosos.split(",") if k]
        assert all(rev[k]["verdict"] == "correct" for k in dudosos)
        res["primary"] = {
            "reviewer": args.revisor,
            "wrong_accepted_findings": len(wrong), "notes": n,
            "sample": "enriched: " + ", ".join(f"{k} {v}" for k, v in strata.items()) + " (only 'resto' is random)",
            "judgment_calls_counted_correct": dudosos,
            "strict_reading_wrong": len(wrong) + len(dudosos),
            "per_100_notes": round(100 * len(wrong) / n, 2), "ci95_exact": [round(100 * lo, 2), round(100 * hi, 2)],
            "by_verdict": dict(collections.Counter(rev[a["key"]]["verdict"] for a in accepted).most_common()),
            # rules/supresion.sql: refusal (N1b) and Nephrology (N1c) only annotate; a "test done" finding removes an
            # order only with a date read in the sentence (N1a); S1c needs a value and a date (n1_nota_confirma.sql).
            "wrong_that_could_change_an_order": sum(1 for a in wrong if could_change(a)),
            "wrong_shown_only_as_a_grey_line_under_the_order": sum(1 for a in wrong if not could_change(a)),
            "wrong_cases": [{"key": a["key"], "label": a["label"], "verdict": rev[a["key"]]["verdict"],
                             "could_change_an_order": could_change(a),
                             "comment": rev[a["key"]].get("comment", "")} for a in wrong],
        }
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    corpus = "LivingNER v6.3.1" if muestra["source"].startswith("LivingNER") else "CodiEsp v1.4"
    md = [f"# Note reader on real published clinical text ({corpus.split()[0]}, {args.conjunto} sample)", "",
          f"Generated by `python3 eval/notas_reales/revisar.py --conjunto {args.conjunto}`. Protocol: `docs/NOTES_REAL_PROTOCOL.md`. "
          f"{n} cases, model {lector.modelo}. Excerpts from {corpus} (CC BY 4.0): `eval/notas_reales/NOTICE.md`.", "",
          "| | |", "|---|---|",
          f"| Model output per case | {', '.join(f'{k} {v}' for k, v in res['model_said'].items())} |",
          f"| Accepted by the code | {res['accepted_findings']} ({', '.join(f'{k} {v}' for k, v in res['accepted_by_label'].items())}) |",
          f"| Missing outputs | {res['missing_outputs']} |",
          "| Model output by stratum (descriptive, not recall) | " + "; ".join(
              f"{k}: " + ", ".join(f"{e} {n}" for e, n in v.items()) for k, v in res["model_said_by_stratum"].items()) + " |",
          f"| Cases cut at 6,000 characters | {long_cut} |", "",
          "## Rejected by the code, by reason", "",
          *[f"- {html.escape(k, quote=False)}: {v}" for k, v in res["rejected_by_reason"].items()], ""]
    if "primary" in res:
        p = res["primary"]
        md += [f"## Primary measure (every accepted finding reviewed by: {p['reviewer']})", "",
               f"**{p['wrong_accepted_findings']} wrong accepted findings in {n} notes: {p['per_100_notes']} per 100 notes "
               f"(exact 95 % CI {p['ci95_exact'][0]}–{p['ci95_exact'][1]}).**",
               f"Sample deliberately enriched for kidney terms ({p['sample']}): not a rate for primary-care notes. "
               f"Counting the {len(p['judgment_calls_counted_correct'])} judgment calls marked correct as wrong: "
               f"{p['strict_reading_wrong']} of {n}.",
               f"Of these, {p['wrong_that_could_change_an_order']} could change an order; "
               f"{p['wrong_shown_only_as_a_grey_line_under_the_order']} would only show as a grey line under the order "
               "(refusal and Nephrology findings never remove anyone; an undated \"test done\" finding does not either). "
               "No accepted finding had a date read from its sentence. A wrong grey line can still mislead the doctor.", "",
               *[f"- {w['key']} ({w['label']}): {w['verdict']}{' — ' + html.escape(w['comment'], quote=False) if w['comment'] else ''}"
                 for w in p["wrong_cases"]], ""]
    out_md.write_text("\n".join(md), encoding="utf-8")
    hoja.write_text(sheet(accepted, LIVINGNER if muestra["source"].startswith("LivingNER") else CODIESP), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
