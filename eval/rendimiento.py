"""Cuenta, sobre un cupo sintético, cuántos pedidos saldrían, por regla, y cuántos se suprimen y por qué.

Uso:
    python eval/rendimiento.py data/synthetic/cupo_250.sql -o eval/results/cupo_250.md

Comprobación de ruido con supuestos declarados (ver la cabecera del extracto), no validación clínica.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import List

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ejecutar import ExtractoInvalido, construir, generar  # noqa: E402


def contar(resultado: dict, n: int) -> dict:
    pedidos = resultado["pedidos"]
    fuera = resultado["fuera_de_la_lista"]
    en_lista = {p["person_id"] for p in pedidos}
    base = set(resultado["baseline_fge_menor_60"])
    motivo = Counter(f["motivo_supresion"].split(":")[0] for f in fuera)   # «Pedido ya pendiente», «Información insuficiente»…
    return {
        "pacientes": n,
        "con_pedido": len(pedidos),
        "por_regla": dict(sorted(Counter(p["regla"] for p in pedidos).items())),
        "con_tambien": sum(1 for p in pedidos if p["tambien"]),
        "hoy_en_consulta": sum(1 for p in pedidos if p["hoy_en_consulta"]),
        "fuera_de_la_lista": dict(motivo),
        "filtro_basico": len(base),
        "filtro_basico_y_reglas": len(base & en_lista),
    }


def a_markdown(c: dict, extracto: str) -> str:
    n = c["pacientes"]
    pct = lambda k: f"{100 * k / n:.0f} %" if n else "—"
    reglas = "\n".join(f"| {r} | {k} |" for r, k in c["por_regla"].items())
    fuera = "\n".join(f"| {m} | {k} |" for m, k in c["fuera_de_la_lista"].items()) or "| — | 0 |"
    return (f"# Rendimiento sobre un cupo sintético\n\nExtracto `{extracto}` · **{n} pacientes** con DM2 y/o HTA.\n\n"
            f"- **{c['con_pedido']} pacientes con un pedido preparado ({pct(c['con_pedido'])})**, "
            f"{c['con_tambien']} de ellos con más de un hallazgo agrupado; {c['hoy_en_consulta']} citados hoy.\n"
            f"- Filtro básico (último FGe <60): {c['filtro_basico']} pacientes, "
            f"{c['filtro_basico_y_reglas']} de ellos también en la lista.\n\n"
            f"| Regla principal | Pacientes |\n|---|---|\n{reglas}\n\n"
            f"| Fuera de la lista | Pacientes |\n|---|---|\n{fuera}\n\n"
            "**Estos recuentos reflejan los parámetros de entrada del generador, no un hallazgo:** "
            "no son la carga de trabajo esperada de un cupo real.\n\n"
            "_Comprobación de ruido con parámetros declarados en la cabecera del extracto (fuente o «supuesto»). "
            "No es validación ni calibración. Datos sintéticos._\n")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("extracto", type=Path)
    ap.add_argument("-o", "--salida", type=Path)
    args = ap.parse_args(argv)
    if not args.extracto.is_file():
        print(f"No existe: {args.extracto}", file=sys.stderr)
        return 2
    try:
        con = construir(args.extracto.read_text(encoding="utf-8"))
        n = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
        c = contar(generar(con), n)
    except ExtractoInvalido as exc:
        print(f"Extracto inválido: {exc}", file=sys.stderr)
        return 2
    md = a_markdown(c, args.extracto.as_posix())
    if args.salida:
        args.salida.write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
