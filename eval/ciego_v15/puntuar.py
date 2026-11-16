"""Score the round-15 blind set (docs/NOTES_REAL_PROTOCOL.md, amendment 10) on two versions of the checks.

    python3 eval/ciego_v15/puntuar.py --set 1 --partir fallo   ->  eval/results/ciego_v15_set1.*         (as run, amendment 10)
    python3 eval/ciego_v15/puntuar.py --set 1                  ->  eval/results/ciego_v15_set1_tuning.*  (tuning only)
    python3 eval/ciego_v15/puntuar.py --set 2                  ->  eval/results/ciego_v15_set2.*         (amendment 12)

--partir fallo: a sentence the reader's splitter cuts counts as missed (amendment 10). --partir trozo (default,
amendment 12): the simulated model points to the first piece that names the expected test, chosen with the round-15
naming for both versions (the model is assumed to point right; the code under test then reads that piece).

"before" = notas/verificar.py as on the commit before round 15 (git show ANTES:notas/verificar.py); "after" = the
working tree. Each sentence is a one-sentence note; the model's output is simulated as pointing to it and naming the
expected test, so this tests the reading rules, not the model.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "eval" / "ciego_v15"
RESULTS = ROOT / "eval" / "results"
ANTES = "b83fa2c"          # pre-registration commit: verificar.py still the signed round-14 version
NOTE_DATE, HOY = "2026-11-01", "2026-11-16"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _num(s):
    return float(s.replace(",", ".")) if s else None


def reading(v, row, partir="trozo", nombra=None):
    """What the code makes of the sentence: (kind, value, unit). kind in value/normal/unreadable/not_acr/bound."""
    salida = {"etiqueta": "ya_realizada", "prueba": row["test"], "fecha_en_nota": None, "frase": 1}
    piezas = v.frases(row["sentence"])
    if len(piezas) != 1:
        if partir == "fallo":
            return ("split", None, None)
        k = next((i for i, t in enumerate(piezas, 1) if nombra(t, row["test"])), 1)
        salida["frase"] = k
    filas = [f for f in v.verificar(row["sentence"], NOTE_DATE, salida, HOY)
             if f["verificada"] == 1 and f.get("prueba") == row["test"]]
    if not filas:
        return ("not_acr" if row["test"] == "CAC" else "rejected", None, None)
    f = filas[0]
    if f.get("valor") is not None:
        return ("value", f["valor"], f.get("unidad"))
    if row["test"] == "FGe":
        return ("bound" if f.get("motivo_rechazo") == "límite, no valor" else "no_value", None, None)
    return ("unreadable", None, None) if f.get("motivo_rechazo") else ("normal", None, None)


def unit_ok(want, got):
    want = (want or "").lower().replace("μ", "µ")
    return got == ("mg/g" if want in ("mg/g", "µg/mg") else want)


def judge(row, got):
    kind, val, unit = got
    exp, want = row["expect"], _num(row["value"])
    if row["test"] == "FGe":
        if kind == "value":
            return "correct" if exp == "value" and abs(val - want) < 1e-6 else "UNSAFE"
        return "correct" if exp == "bound" and kind == "bound" else "missed"
    if kind == "value":
        return "correct" if exp == "value" and abs(val - want) < 1e-6 and unit_ok(row["unit"], unit) else "UNSAFE"
    if kind == "normal":
        return "correct" if exp == "normal" else "UNSAFE"
    if exp == "not_acr":
        return "correct" if kind == "not_acr" else "grey_line"
    return "correct" if kind == exp else "missed"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", type=int, choices=[1, 2, 3], default=2)
    ap.add_argument("--partir", choices=["fallo", "trozo"], default="trozo")
    ap.add_argument("--firmado", action="store_true",
                    help="score the signed V2-V7 code into *_signed (after the sets were scored: descriptive)")
    args = ap.parse_args(argv)
    if args.set >= 2 and args.partir == "fallo":
        raise SystemExit("sets 2 and 3 are scored with --partir trozo (amendments 12, 14)")
    nombre = f"ciego_v15_set{args.set}" + ("_signed" if args.firmado else
                                           "_tuning" if args.set == 1 and args.partir == "trozo" else "")
    OUT = RESULTS / nombre
    with (HERE / f"frases_set{args.set}.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    with tempfile.TemporaryDirectory() as d:
        old = Path(d) / "verificar_antes.py"
        old.write_bytes(subprocess.run(["git", "show", f"{ANTES}:notas/verificar.py"], cwd=ROOT, check=True,
                                       capture_output=True).stdout)
        versions = {"before": _load(old, "verificar_antes"), "after": _load(ROOT / "notas" / "verificar.py", "verificar_despues")}
        despues = versions["after"]
        nombra = lambda t, prueba: prueba in despues._pruebas_nombradas(t)  # noqa: E731
        res = {"set": f"eval/ciego_v15/frases_set{args.set}.csv", "split_handling": args.partir, "rows": len(rows), "before_commit": ANTES, "versions": {}, "cases": []}
        for name, v in versions.items():
            tally = {}
            for r in rows:
                got = reading(v, r, args.partir, nombra)
                verdict = judge(r, got)
                key = f"{r['test']}/{r['expect']}"
                tally.setdefault(key, {}).setdefault(verdict, 0)
                tally[key][verdict] += 1
                if name == "after" or verdict == "UNSAFE":
                    res["cases"].append({"id": r["id"], "version": name, "expect": key, "value": r["value"],
                                         "got": list(got), "verdict": verdict}) if verdict != "correct" else None
            unsafe = sum(t.get("UNSAFE", 0) for t in tally.values())
            res["versions"][name] = {"by_expected": tally, "unsafe": unsafe,
                                     "acr_values_correct": tally.get("CAC/value", {}).get("correct", 0),
                                     "not_acr_as_grey_line": tally.get("CAC/not_acr", {}).get("grey_line", 0)}
    res["pass"] = res["versions"]["after"]["unsafe"] == 0
    OUT.with_suffix(".json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    B, A = res["versions"]["before"], res["versions"]["after"]
    n_val = sum(1 for r in rows if r["test"] == "CAC" and r["expect"] == "value")
    titulo = {"ciego_v15_set1": "set 1, as run (amendment 10)", "ciego_v15_set1_tuning": "set 1 re-scored after the "
              "fixes: TUNING DATA, not a test", "ciego_v15_set2": "set 2 (amendment 12)", "ciego_v15_set3": "set 3 (amendment 14)"}.get(nombre, f"set {args.set}, "
              "re-scored on the SIGNED code (V2-V7, V1 held) after every set had been scored: descriptive, not a test")
    md = [f"# Round 15 blind {titulo}", "",
          f"Generated by `python3 eval/ciego_v15/puntuar.py --set {args.set} --partir {args.partir}{' --firmado' if args.firmado else ''}`. {len(rows)} synthetic sentences written blind by an AI agent "
          "(not a physician); the model's pointing is simulated, so this tests the reading rules only.", "",
          f"| | Before (round 14, signed) | After (round 15{', signed V2–V7' if args.firmado else ', as tested'}) |", "|---|---|---|",
          f"| **Unsafe readings (primary; pass = 0 after)** | {B['unsafe']} | **{A['unsafe']}** |",
          f"| ACR values read correctly (of {n_val}) | {B['acr_values_correct']} | {A['acr_values_correct']} |",
          f"| Not an ACR, but accepted as one (grey line) | {B['not_acr_as_grey_line']} | {A['not_acr_as_grey_line']} |", "",
          f"**Result: {'PASS' if res['pass'] else 'FAIL'}.**", "", "## By expected reading (after)", ""]
    for k, t in sorted(A["by_expected"].items()):
        md.append(f"- {k}: " + ", ".join(f"{v} {n}" for v, n in sorted(t.items())))
    md.append("")
    OUT.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
