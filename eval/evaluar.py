"""Compara las reglas y el filtro básico con etiquetas escritas ANTES de ejecutar las reglas.

Uso:
    python eval/evaluar.py data/synthetic/demo_seed.sql data/synthetic/demo_etiquetas.csv -o eval/results/demo.md
    (añade --exigir para que la CI falle si alguna etiqueta no coincide)

Etiquetas (CSV con cabecera): person_id, esperado [, fuente]
    esperado ∈ S1a, S1b, S3, S3c (regla principal esperada) · fuera (debe quedar fuera de la lista) · ninguno

Resultado = verificación de software frente a las reglas firmadas, no validación clínica.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ejecutar import ExtractoInvalido, agregar_opciones_lector, cerrar_lector, construir, crear_lector, generar  # noqa: E402

REGLAS = {"S1a", "S1b", "S1c", "S3", "S3c"}
VALIDOS = REGLAS | {"fuera", "ninguno"}


class Caso(NamedTuple):
    person_id: int
    esperado: str
    obtenido: str
    baseline: bool


def leer_etiquetas(ruta: Path) -> Dict[int, str]:
    etiquetas: Dict[int, str] = {}
    with ruta.open(encoding="utf-8", newline="") as f:
        for n, fila in enumerate(csv.DictReader(f), start=2):
            try:
                pid, esp = int(fila["person_id"]), fila["esperado"].strip()
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{ruta}:{n}: fila no válida ({exc})") from exc
            if esp not in VALIDOS:
                raise ValueError(f"{ruta}:{n}: «{esp}» no es una etiqueta válida ({', '.join(sorted(VALIDOS))})")
            if pid in etiquetas:
                raise ValueError(f"{ruta}:{n}: person_id {pid} repetido")
            etiquetas[pid] = esp
    if not etiquetas:
        raise ValueError(f"{ruta}: no hay etiquetas")
    return etiquetas


def comparar(resultado: dict, etiquetas: Dict[int, str]) -> List[Caso]:
    principal = {p["person_id"]: p["regla"] for p in resultado["pedidos"]}
    fuera = {f["person_id"] for f in resultado["fuera_de_la_lista"]}
    baseline = set(resultado["baseline_fge_menor_60"])
    casos = []
    for pid, esp in sorted(etiquetas.items()):
        obtenido = principal.get(pid) or ("fuera" if pid in fuera else "ninguno")
        casos.append(Caso(pid, esp, obtenido, pid in baseline))
    return casos


def resumen(casos: List[Caso]) -> dict:
    def tabla(marca) -> dict:
        tp = sum(1 for c in casos if c.esperado in REGLAS and marca(c))
        fp = sum(1 for c in casos if c.esperado not in REGLAS and marca(c))
        fn = sum(1 for c in casos if c.esperado in REGLAS and not marca(c))
        tn = sum(1 for c in casos if c.esperado not in REGLAS and not marca(c))
        return {"avisos_correctos": tp, "falsos_avisos": fp, "perdidos": fn, "callados_correctos": tn}

    return {
        "casos": len(casos),
        "coinciden_exactamente": sum(1 for c in casos if c.esperado == c.obtenido),
        "reglas": {**tabla(lambda c: c.obtenido in REGLAS),
                   "regla_distinta": sum(1 for c in casos if c.esperado in REGLAS and c.obtenido in REGLAS
                                         and c.esperado != c.obtenido)},
        "filtro_basico_fge_menor_60": tabla(lambda c: c.baseline),
        "discrepancias": [c._asdict() for c in casos if c.esperado != c.obtenido],
    }


def a_markdown(r: dict, extracto: str, etiquetas: str) -> str:
    reg, base = r["reglas"], r["filtro_basico_fge_menor_60"]
    filas = [
        "| | Reglas | Filtro básico (último FGe <60) |",
        "|---|---|---|",
    ] + [f"| {k.replace('_', ' ').capitalize()} | {reg[k]} | {base[k]} |"
         for k in ("avisos_correctos", "falsos_avisos", "perdidos", "callados_correctos")]
    disc = "\n".join(f"- person_id {d['person_id']}: esperado {d['esperado']}, obtenido {d['obtenido']}"
                     for d in r["discrepancias"]) or "- Ninguna."
    return (f"# Evaluación frente a etiquetas\n\n"
            f"Extracto `{extracto}` · etiquetas `{etiquetas}` (escritas antes de ejecutar las reglas).\n\n"
            f"**{r['coinciden_exactamente']} de {r['casos']}** casos coinciden exactamente "
            f"(regla principal o «fuera de la lista»). Regla distinta de la esperada: {reg['regla_distinta']}.\n\n"
            + "\n".join(filas) +
            f"\n\n## Discrepancias\n{disc}\n\n"
            "_Verificación de software frente a las reglas firmadas, no validación clínica. Datos sintéticos._\n")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("extracto", type=Path)
    ap.add_argument("etiquetas", type=Path)
    ap.add_argument("-o", "--salida", type=Path, help="archivo .md; junto a él se escribe el .json")
    ap.add_argument("--exigir", action="store_true", help="código de salida 1 si alguna etiqueta no coincide")
    agregar_opciones_lector(ap)
    args = ap.parse_args(argv)
    for ruta in (args.extracto, args.etiquetas):
        if not ruta.is_file():
            print(f"No existe: {ruta}", file=sys.stderr)
            return 2
    try:
        etiquetas = leer_etiquetas(args.etiquetas)
        lector = crear_lector(args)
        r = resumen(comparar(generar(construir(args.extracto.read_text(encoding="utf-8"), lector=lector)), etiquetas))
    except (ExtractoInvalido, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    cerrar_lector(lector, args)
    md = a_markdown(r, args.extracto.as_posix(), args.etiquetas.as_posix())
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(md, encoding="utf-8")
        args.salida.with_suffix(".json").write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(md)
    sin_grabar = len(getattr(lector, "sin_grabar", None) or [])
    if args.exigir and sin_grabar:
        print(f"Error: {sin_grabar} notas sin salida grabada: la grabación no corresponde a este extracto", file=sys.stderr)
        return 1
    return 1 if args.exigir and r["discrepancias"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
