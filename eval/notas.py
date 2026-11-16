"""Evalúa el lector de notas nota por nota y su efecto en la lista (NOTE_READER_SPEC §6).

Uso:
    python3 eval/notas.py data/synthetic/notas_dev data/synthetic/notas_dev/salidas_oraculo.jsonl -o eval/results/notas_dev.md

La carpeta tiene extracto.sql, etiquetas_notas.csv (note_id, etiqueta, prueba) y etiquetas.csv (lista esperada con notas).
Cuenta, por etiqueta: correctas / falsas / perdidas, DESPUÉS de las comprobaciones del código; cuántas citas rechazó
el código; y las exclusiones equivocadas (pacientes sacados de la lista que debían quedarse): el número de seguridad.
Verificación de software sobre notas sintéticas, no validación clínica.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ejecutar import ExtractoInvalido, construir, generar  # noqa: E402
from eval.evaluar import leer_etiquetas  # noqa: E402
from notas.leer import LectorGrabado  # noqa: E402

ETIQUETAS = ("ya_realizada", "rechazo", "nefrologia")


def evaluar(carpeta: Path, grabadas: Path, etiquetas: str = "etiquetas.csv") -> Dict[str, Any]:
    lector = LectorGrabado(grabadas)
    con = construir((carpeta / "extracto.sql").read_text(encoding="utf-8"), lector=lector)
    res = generar(con)
    esperadas = {int(f["note_id"]): f["etiqueta"] for f in
                 csv.DictReader((carpeta / "etiquetas_notas.csv").open(encoding="utf-8", newline=""))}
    obtenidas: Dict[int, str] = {}
    rechazadas = 0
    for h in con.execute("SELECT note_id, etiqueta, verificada, motivo_rechazo FROM nota_hallazgo"):
        if h["verificada"]:
            obtenidas[h["note_id"]] = h["etiqueta"]
        elif h["motivo_rechazo"] and h["motivo_rechazo"] != "el modelo no encontró nada":
            rechazadas += 1
    por_etiqueta = {e: Counter() for e in ETIQUETAS}
    errores: List[str] = []
    for nid, esp in sorted(esperadas.items()):
        obt = obtenidas.get(nid, "ninguna")
        if esp == obt and esp != "ninguna":
            por_etiqueta[esp]["correctas"] += 1
        else:
            if obt != "ninguna":
                por_etiqueta[obt]["falsas"] += 1
            if esp != "ninguna":
                por_etiqueta[esp]["perdidas"] += 1
            if esp != obt:
                errores.append(f"nota {nid}: esperada «{esp}», obtenida «{obt}»")
    lista = leer_etiquetas(carpeta / etiquetas)
    en_lista = {p["person_id"] for p in res["pedidos"]}
    sacados = {f["person_id"] for f in res["fuera_de_la_lista"]} - en_lista
    equivocadas = sorted(pid for pid in sacados if lista.get(pid) not in ("fuera", None))
    return {"modelo": lector.modelo, "notas": len(esperadas), "sin_salida_grabada": len(lector.sin_grabar),
            "por_etiqueta": {e: dict(c) for e, c in por_etiqueta.items()}, "citas_rechazadas": rechazadas,
            "exclusiones_equivocadas": equivocadas, "errores": errores}


def a_markdown(r: Dict[str, Any]) -> str:
    filas = "\n".join(f"| {e} | {c.get('correctas', 0)} | {c.get('falsas', 0)} | {c.get('perdidas', 0)} |"
                      for e, c in r["por_etiqueta"].items())
    errores = "\n".join(f"- {e}" for e in r["errores"]) or "- Ninguno."
    return (f"# Lector de notas · {r['modelo']}\n\n{r['notas']} notas · sin salida grabada: {r['sin_salida_grabada']} · "
            f"citas rechazadas por el código: {r['citas_rechazadas']}\n\n"
            f"**Exclusiones equivocadas (pacientes sacados de la lista que debían quedarse): "
            f"{len(r['exclusiones_equivocadas'])}** {r['exclusiones_equivocadas'] or ''}\n\n"
            f"| Etiqueta (tras las comprobaciones) | Correctas | Falsas | Perdidas |\n|---|---|---|---|\n{filas}\n\n"
            f"## Errores\n{errores}\n\n_Notas sintéticas. Verificación de software, no validación clínica._\n")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("carpeta", type=Path)
    ap.add_argument("grabadas", type=Path)
    ap.add_argument("-o", "--salida", type=Path)
    ap.add_argument("--etiquetas", default="etiquetas.csv", help="lista esperada con notas, dentro de la carpeta")
    args = ap.parse_args(argv)
    try:
        r = evaluar(args.carpeta, args.grabadas, args.etiquetas)
    except (ExtractoInvalido, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    md = a_markdown(r)
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(md, encoding="utf-8")
        args.salida.with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
