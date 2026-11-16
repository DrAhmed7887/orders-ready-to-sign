"""Draw the fixed sample of real case texts (protocol docs/NOTES_REAL_PROTOCOL.md, amendment 1).

    python3 eval/notas_reales/muestra.py   ->  eval/notas_reales/muestra.json  (case ids, stratum, SHA-256; no text)

Strata, assigned in this order (a case goes to the first that matches), seed 20261116:
  albumin    every case naming urine albumin (microalbumin*, albuminuria, cociente albúmina, mg/g)   all of them
  nefrologia mentions Nephrology                                                                       40
  fg         a creatinine value in mg/dl or an eGFR / "filtrado" value                                 70
  rechazo    "rechaz*", "no desea", "se niega"                                                         40
  resto      everything else                                                                 up to 300 in total
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "eval" / "notas_reales" / "raw"
OUT = ROOT / "eval" / "notas_reales" / "muestra.json"
SEED, TOTAL = 20261116, 300
STRATA = [
    ("albumin", r"microalbumin|albuminuria|cociente\s+(?:de\s+)?alb[uú]mina|\bmg/g\b", None),
    ("nefrologia", r"nefrolog[ií]a", 40),
    ("fg", r"creatinina[^.\n]{0,40}\d+[.,]?\d*\s*mg/d[lL]|(?:\bFGe?\b|filtrado glomerular)[^.\n]{0,40}\d+", 70),
    ("rechazo", r"rechaz|no desea|se niega", 40),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--excluir", type=Path, action="append", default=[], help="earlier sample(s) whose cases are left out")
    ap.add_argument("--semilla", type=int, default=SEED)
    ap.add_argument("--salida", type=Path, default=OUT)
    ap.add_argument("--corpus", choices=["codiesp", "livingner"], default="codiesp",
                    help="livingner: draw from raw/livingner_* only, leaving out near-duplicates of ANY CodiEsp text")
    ap.add_argument("--sin-casi-duplicados", action="store_true",
                    help="also leave out a case sharing >= 50 %% of its 8-word shingles with an excluded case (round 13, E2)")
    args = ap.parse_args(argv)
    used = {c["id"] for e in args.excluir for c in json.loads(e.read_text(encoding="utf-8"))["cases"]}
    livingner = args.corpus == "livingner"
    files = [f for f in sorted(RAW.glob("*/*.txt"))
             if f.parent.name.startswith("livingner_") == livingner and f"{f.parent.name}/{f.stem}" not in used]
    near_dupes = []
    if args.sin_casi_duplicados and (used or livingner):
        def shingles(text):
            w = re.findall(r"\w+", text.lower())
            return {" ".join(w[i:i + 8]) for i in range(max(0, len(w) - 7))}
        seen = set()
        base = ([f"{f.parent.name}/{f.stem}" for f in RAW.glob("*/*.txt") if not f.parent.name.startswith("livingner_")]
                if livingner else []) + sorted(used)
        for cid in base:
            seen |= shingles((RAW / f"{cid}.txt").read_text(encoding="utf-8"))
        keep = []
        for f in files:
            s = shingles(f.read_text(encoding="utf-8"))
            if s and len(s & seen) / len(s) >= 0.5:
                near_dupes.append(f"{f.parent.name}/{f.stem}")
            else:
                keep.append(f)
                seen |= s   # within LivingNER too: the same case in two splits is kept once
        files = keep
    if not files:
        raise SystemExit("no texts: run eval/notas_reales/fetch.py first")
    pools = {name: [] for name, _, _ in STRATA} | {"resto": []}
    for f in files:
        t = f.read_text(encoding="utf-8")
        name = next((n for n, p, _ in STRATA if re.search(p, t, re.I)), "resto")
        pools[name].append(f)
    rng = random.Random(args.semilla)
    chosen = []
    for name, _, k in STRATA:
        pool = pools[name]
        take = list(pool) if k is None else rng.sample(pool, min(k, len(pool)))
        chosen += [(name, f) for f in take]
    chosen += [("resto", f) for f in rng.sample(pools["resto"], TOTAL - len(chosen))]
    rng.shuffle(chosen)
    out = {
        "source": ("LivingNER v6.3.1, doi:10.5281/zenodo.7684093, CC BY 4.0" if livingner
                   else "CodiEsp v1.4, doi:10.5281/zenodo.3837305, CC BY 4.0"),
        "seed": args.semilla,
        "excluded_earlier_samples": [str(e) for e in args.excluir], "excluded_cases": len(used),
        "pool_sizes": {k: len(v) for k, v in pools.items()},
        "cases": [{"id": f"{f.parent.name}/{f.stem}", "stratum": name,
                   "sha256": hashlib.sha256(f.read_text(encoding="utf-8").encode("utf-8")).hexdigest()}
                  for name, f in chosen],
    }
    if args.sin_casi_duplicados:   # only then, so earlier samples regenerate byte for byte
        out = {**{k: v for k, v in out.items() if k != "cases"}, "excluded_near_duplicates": len(near_dupes),
               "cases": out["cases"]}
    args.salida.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["pool_sizes"]), "->", len(out["cases"]), "cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
