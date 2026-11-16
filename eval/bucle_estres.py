"""Bucle de estrés: ejecuta TODOS los conjuntos frente a sus etiquetas y apunta las métricas de la vuelta.

Uso:
    python3 eval/bucle_estres.py --vuelta 2 --nota "qué se arregló"      # añade la vuelta a eval/stress_loop_report.json
    python3 eval/bucle_estres.py --exigir                                # sin escribir: código 1 si algo no coincide

Por conjunto: aciertos (TP), falsos avisos (FP), perdidos (FN), fuera de la lista (suprimidos), «información
insuficiente» (abstenciones), exclusiones equivocadas (debían estar en la lista y quedaron fuera) y tiempo.
Verificación de software sobre datos sintéticos, no validación clínica.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ejecutar import construir, generar  # noqa: E402
from eval.evaluar import REGLAS, comparar, leer_etiquetas, resumen  # noqa: E402
from notas.leer import LectorGrabado  # noqa: E402

S = "data/synthetic"
QWEN = "salidas_qwen3-4b-instruct-2507.jsonl"
QWEN38 = "salidas_qwen3.8-27b.jsonl"
# nombre, extracto, etiquetas, salidas grabadas del lector (o None)
CONJUNTOS: List[Tuple[str, str, str, Optional[str]]] = [
    ("demo_seed", f"{S}/demo_seed.sql", f"{S}/demo_etiquetas.csv", None),
    ("ciego", f"{S}/ciego/extracto.sql", f"{S}/ciego/etiquetas.csv", None),
    ("notas_dev · sin notas", f"{S}/notas_dev/extracto.sql", f"{S}/notas_dev/etiquetas_sin_notas.csv", None),
    ("notas_dev · oráculo", f"{S}/notas_dev/extracto.sql", f"{S}/notas_dev/etiquetas.csv", f"{S}/notas_dev/salidas_oraculo.jsonl"),
    ("notas_dev · Qwen3-4B", f"{S}/notas_dev/extracto.sql", f"{S}/notas_dev/etiquetas.csv", f"{S}/notas_dev/{QWEN}"),
    ("aguja · sin notas", f"{S}/aguja/extracto.sql", f"{S}/aguja/etiquetas_sin_notas.csv", None),
    ("aguja · oráculo", f"{S}/aguja/extracto.sql", f"{S}/aguja/etiquetas.csv", f"{S}/aguja/salidas_oraculo.jsonl"),
    ("aguja · Qwen3-4B", f"{S}/aguja/extracto.sql", f"{S}/aguja/etiquetas.csv", f"{S}/aguja/{QWEN}"),
    ("cupo_espanol_1000 · sin notas", f"{S}/cupo_espanol_1000/extracto.sql", f"{S}/cupo_espanol_1000/etiquetas_sin_notas.csv", None),
    ("cupo_espanol_1000 · oráculo", f"{S}/cupo_espanol_1000/extracto.sql", f"{S}/cupo_espanol_1000/etiquetas_cupo_1000.csv",
     f"{S}/cupo_espanol_1000/salidas_oraculo.jsonl"),
    ("cupo_espanol_1000 · Qwen3-4B", f"{S}/cupo_espanol_1000/extracto.sql", f"{S}/cupo_espanol_1000/etiquetas_cupo_1000.csv",
     f"{S}/cupo_espanol_1000/{QWEN}"),
    # Comparación informativa (no cuenta para --exigir): Qwen 3.8 27B en RWTHgpt (KI:connect NRW), sin control de semilla.
    ("notas_dev · Qwen 3.8 (informativo)", f"{S}/notas_dev/extracto.sql", f"{S}/notas_dev/etiquetas.csv", f"{S}/notas_dev/{QWEN38}"),
    ("aguja · Qwen 3.8 (informativo)", f"{S}/aguja/extracto.sql", f"{S}/aguja/etiquetas.csv", f"{S}/aguja/{QWEN38}"),
    ("cupo_espanol_1000 · Qwen 3.8 (informativo)", f"{S}/cupo_espanol_1000/extracto.sql",
     f"{S}/cupo_espanol_1000/etiquetas_cupo_1000.csv", f"{S}/cupo_espanol_1000/{QWEN38}"),
]
INFORME = RAIZ / "eval" / "stress_loop_report.json"


def medir(extracto: str, etiquetas: str, grabadas: Optional[str]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    lector = LectorGrabado(RAIZ / grabadas) if grabadas else None
    res = generar(construir((RAIZ / extracto).read_text(encoding="utf-8"), lector=lector))
    esperadas = leer_etiquetas(RAIZ / etiquetas)
    r = resumen(comparar(res, esperadas))
    en_lista = {p["person_id"] for p in res["pedidos"]}
    fuera = {f["person_id"] for f in res["fuera_de_la_lista"]} - en_lista
    return {
        "pacientes_etiquetados": r["casos"],
        "coinciden": r["coinciden_exactamente"],
        "TP": r["reglas"]["avisos_correctos"],
        "FP": r["reglas"]["falsos_avisos"],
        "FN": r["reglas"]["perdidos"],
        "regla_distinta": r["reglas"]["regla_distinta"],
        "suprimidos": len(fuera),
        "abstenciones_informacion_insuficiente": sum(1 for f in res["fuera_de_la_lista"]
                                                     if f["motivo_supresion"].startswith("Información insuficiente")),
        "exclusiones_equivocadas": sorted(pid for pid in fuera if esperadas.get(pid) in REGLAS),
        "notas_sin_salida_grabada": len(getattr(lector, "sin_grabar", []) or []),
        "discrepancias": [f"{d['person_id']}: esperado {d['esperado']}, obtenido {d['obtenido']}" for d in r["discrepancias"]],
        "segundos": round(time.perf_counter() - t0, 3),
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--vuelta", type=int, help="número de vuelta; sin él no se escribe el informe")
    ap.add_argument("--nota", default="", help="qué cambió en esta vuelta")
    ap.add_argument("--exigir", action="store_true")
    args = ap.parse_args(argv)
    filas: Dict[str, Any] = {}
    for nombre, extracto, etiquetas, grabadas in CONJUNTOS:
        if grabadas and not (RAIZ / grabadas).is_file():
            filas[nombre] = {"omitido": f"no existe {grabadas}"}
            continue
        filas[nombre] = medir(extracto, etiquetas, grabadas)
    for nombre, m in filas.items():
        if "omitido" in m:
            print(f"{nombre:34s} omitido ({m['omitido']})")
        else:
            print(f"{nombre:34s} {m['coinciden']:4d}/{m['pacientes_etiquetados']:<4d} TP {m['TP']:3d} FP {m['FP']} FN {m['FN']} "
                  f"suprimidos {m['suprimidos']:3d} insuf. {m['abstenciones_informacion_insuficiente']:2d} "
                  f"excl. equivocadas {len(m['exclusiones_equivocadas'])} · {m['segundos']} s")
            for d in m["discrepancias"][:10]:
                print(f"    {d}")
    if args.vuelta is not None:
        informe = json.loads(INFORME.read_text(encoding="utf-8")) if INFORME.is_file() else {"vueltas": []}
        informe["vueltas"] = [v for v in informe["vueltas"] if v["vuelta"] != args.vuelta]
        informe["vueltas"].append({"vuelta": args.vuelta, "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                                   "nota": args.nota, "conjuntos": filas})
        informe["vueltas"].sort(key=lambda v: v["vuelta"])
        INFORME.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"→ {INFORME.relative_to(RAIZ)} (vuelta {args.vuelta})")
    malos = [n for n, m in filas.items() if "omitido" not in m and "informativo" not in n
             and (m["discrepancias"] or m["notas_sin_salida_grabada"] or m["exclusiones_equivocadas"])]
    # Una exclusión equivocada nunca es informativa: con cualquier modelo, falla.
    malos += [n for n, m in filas.items() if "omitido" not in m and "informativo" in n and m["exclusiones_equivocadas"]]
    return 1 if args.exigir and malos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
