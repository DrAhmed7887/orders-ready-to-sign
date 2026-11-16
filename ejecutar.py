"""Ejecuta las reglas sobre un extracto y escribe pedidos.json para la pantalla del médico.

Uso:
    python ejecutar.py data/synthetic/demo_seed.sql -o ui/pedidos.json

Solo biblioteca estándar. El mismo extracto da siempre la misma salida (idempotente):
el identificador de cada pedido depende de la regla, la persona y la fecha del dato de origen.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent
ESQUEMA = RAIZ / "data" / "schema.sql"
REGLAS = [
    "00_parametros.sql",
    "s1b_albuminuria_sin_repetir.sql",   # antes que S1a: si S1b ya pide repetir el CAC, S1a no pide otro
    "s1a_cac_pendiente.sql",
    "s3_fge_en_descenso.sql",
]
TRAS_NOTAS = [                           # después del lector de notas (si lo hay)
    "n1_nota_confirma.sql",              # N1a enmendada: CAC alterado en nota → nunca retira; S1c persistente
    "supresion.sql",
]
BASELINE = "baseline_fge_menor_60.sql"
GRUPOS = {1: "Empeorando", 2: "Sin seguimiento", 3: "Prueba pendiente"}
DIAGNOSTICOS = {"DM2": "Diabetes tipo 2", "DM1": "Diabetes tipo 1", "HTA": "Hipertensión", "ERC": "ERC codificada"}
SEXO = {8532: "Mujer", 8507: "Hombre"}   # OMOP gender_concept_id


class ExtractoInvalido(ValueError):
    """El extracto no se puede procesar (falta la fecha de referencia, etc.)."""


# Columnas de fecha que usan las reglas: deben ser fechas reales en formato AAAA-MM-DD.
FECHAS = [
    ("extract_meta", "fecha_referencia"),
    ("measurement", "measurement_date"),
    ("condition_occurrence", "condition_start_date"),
    ("visit_occurrence", "visit_start_date"),
    ("drug_exposure", "drug_exposure_start_date"),
    ("pedido_pendiente", "fecha_pedido"),
    ("note", "note_date"),
]


def _validar(con: sqlite3.Connection) -> None:
    """Rechaza el extracto antes de ejecutar las reglas si algo impediría decidir con seguridad."""
    filas = con.execute("SELECT COUNT(*) FROM extract_meta").fetchone()[0]
    if filas != 1:
        raise ExtractoInvalido("extract_meta debe tener exactamente una fila con fecha_referencia")
    for tabla, col in FECHAS:  # nombres fijos de esta lista, nunca entrada externa
        mala = con.execute(
            f"SELECT {col} FROM {tabla} WHERE date({col}) IS NULL OR date({col}) <> {col} LIMIT 1"
        ).fetchone()
        if mala:
            raise ExtractoInvalido(f"{tabla}.{col}: fecha no válida «{mala[0]}» (se espera AAAA-MM-DD)")
    # SQLite guarda un texto («<3», «N/A») en una columna REAL tal cual, y un texto es «mayor» que cualquier número.
    texto = con.execute(
        "SELECT measurement_id, value_as_number FROM measurement "
        "WHERE typeof(value_as_number) NOT IN ('real', 'integer', 'null') LIMIT 1"
    ).fetchone()
    if texto:
        raise ExtractoInvalido(f"measurement {texto[0]}: resultado no numérico «{texto[1]}» en value_as_number")
    huerfano = con.execute("PRAGMA foreign_key_check").fetchone()
    if huerfano:
        raise ExtractoInvalido(f"{huerfano[0]}: registro que apunta a una fila inexistente de {huerfano[2]}")


# El extracto solo puede insertar filas en las tablas de datos: ni crear, ni borrar, ni adjuntar archivos.
TABLAS_DATOS = {"person", "visit_occurrence", "condition_occurrence", "measurement", "drug_exposure",
                "observation", "pedido_pendiente", "extract_meta", "note"}   # nota_hallazgo NO: la escribe el lector
_PERMITIDO = {sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_TRANSACTION}


def _solo_insertar(accion: int, arg1: Optional[str], arg2: Optional[str], db: Optional[str], disparador: Optional[str]) -> int:
    if accion == sqlite3.SQLITE_INSERT and arg1 in TABLAS_DATOS and db == "main":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_OK if accion in _PERMITIDO else sqlite3.SQLITE_DENY


def construir(extracto_sql: str, lector: Optional[Callable[[str], Any]] = None) -> sqlite3.Connection:
    """Carga esquema + extracto + reglas en una base en memoria.

    Con `lector` (ver notas/leer.py), después de las reglas y antes de la supresión se leen las notas de los
    candidatos; lo que pasa las comprobaciones del código (N1) entra en nota_hallazgo. Sin lector, nada cambia.
    """
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    con.set_authorizer(_solo_insertar)
    try:
        con.executescript(extracto_sql)
    except sqlite3.Error as exc:
        raise ExtractoInvalido(f"El extracto no cumple el esquema o hace algo más que insertar datos: {exc}") from exc
    finally:
        # set_authorizer(None) solo limpia desde Python 3.11; en 3.9 se deja uno que lo permite todo.
        con.set_authorizer(lambda *_: sqlite3.SQLITE_OK)
    _validar(con)
    try:
        for nombre in REGLAS:
            con.executescript((RAIZ / "rules" / nombre).read_text(encoding="utf-8"))
        if lector is not None:
            from notas.leer import leer_notas
            leer_notas(con, lector)
        for nombre in TRAS_NOTAS:
            con.executescript((RAIZ / "rules" / nombre).read_text(encoding="utf-8"))
    except sqlite3.Error as exc:
        raise ExtractoInvalido(f"Las reglas no pudieron ejecutarse sobre este extracto: {exc}") from exc
    return con


def _procedencia(con: sqlite3.Connection, person_id: int) -> List[Dict[str, Any]]:
    """Todos los CAC y FGe de la ventana de la tendencia, más el último de cada uno aunque sea antiguo."""
    filas = con.execute(
        """WITH corte AS (
             SELECT date(hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro
                                      WHERE clave = 'meses_ventana_fge') || ' months') AS desde FROM ref)
           SELECT 'CAC' AS prueba, fecha, valor, unidad FROM cac, corte
           WHERE person_id = :p AND (fecha >= corte.desde
                 OR measurement_id = (SELECT measurement_id FROM cac_ultimo WHERE person_id = :p))
           UNION ALL
           SELECT 'FGe', fecha, valor, unidad FROM fge, corte
           WHERE person_id = :p AND (fecha >= corte.desde
                 OR fecha = (SELECT fecha FROM fge_ultimo WHERE person_id = :p))
           ORDER BY fecha DESC, prueba""",
        {"p": person_id},
    )
    return [dict(f) for f in filas]


def _fila(c: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": f"{c['regla']}-{c['person_id']}-{c['fecha_origen'] or 'sin-fecha'}",
        "regla": c["regla"],
        "grupo": c["grupo"],
        "prioridad": c["prioridad"],
        "prueba": c["prueba"],
        "motivo": c["motivo"],
        "pedido": c["pedido"],
        "nota": c["nota"],
        "fecha_origen": c["fecha_origen"],
    }


def _fuentes(con: sqlite3.Connection, person_id: int) -> List[Dict[str, str]]:
    """De dónde sale cada dato del pedido, tabla por tabla del extracto: la señal está repartida entre varias."""
    diag = [r[0] for r in con.execute(
        "SELECT DISTINCT condition_source_value FROM condition_occurrence WHERE person_id = ? ORDER BY 1", (person_id,))]
    erc = any(d.startswith("N18") for d in diag)
    cac = [f"CAC {r['valor']:g} {r['unidad']} ({r['fecha']})" for r in con.execute(
        "SELECT valor, unidad, fecha FROM cac WHERE person_id = ? AND valor IS NOT NULL ORDER BY fecha DESC LIMIT 3", (person_id,))]
    fge = [f"FGe {r['valor']:g} ({r['fecha']})" for r in con.execute(
        "SELECT valor, fecha FROM fge WHERE person_id = ? ORDER BY fecha DESC LIMIT 3", (person_id,))]
    farm = [f"{r[0]} ({r[1]})" for r in con.execute(
        "SELECT drug_source_value, drug_exposure_start_date FROM drug_exposure WHERE person_id = ? "
        "ORDER BY drug_exposure_start_date DESC LIMIT 3", (person_id,))]
    pend = [f"{r[0]} pedido el {r[1]}" for r in con.execute(
        "SELECT prueba, fecha_pedido FROM pendiente_vigente WHERE person_id = ?", (person_id,))]
    notas = [f"nota del {r[0]}: «{r[1]}»" for r in con.execute(
        "SELECT DISTINCT note_date, cita FROM nota_hallazgo WHERE person_id = ? AND verificada = 1 ORDER BY note_date",
        (person_id,))]
    return [
        {"tabla": "condition_occurrence", "dato": (", ".join(diag) or "sin diagnósticos") + ("" if erc else " · sin N18 (ERC sin codificar)")},
        {"tabla": "measurement", "dato": " · ".join(cac + fge) or "sin CAC ni FGe"},
        {"tabla": "drug_exposure", "dato": " · ".join(farm) or "sin dispensaciones registradas"},
        {"tabla": "pedido_pendiente", "dato": " · ".join(pend) or "ningún pedido vigente"},
        {"tabla": "note", "dato": " · ".join(notas) or "ninguna nota con una cita comprobada"},
    ]


def _evolutivos(con: sqlite3.Connection, person_id: int) -> List[Dict[str, Any]]:
    """Las notas recientes del paciente tal como están en el extracto (≤12 meses, las 3 últimas), con la frase
    que el código comprobó, si la hay. La página las enseña como «Hoja de seguimiento»."""
    filas = con.execute(
        """SELECT n.note_id, n.note_date, n.note_text FROM note n CROSS JOIN ref
           WHERE n.person_id = ? AND n.note_date <= ref.hoy AND n.note_date >= date(ref.hoy, '-12 months')
           ORDER BY n.note_date DESC, n.note_id DESC LIMIT 3""", (person_id,)).fetchall()
    citas = {r[0]: r[1] for r in con.execute(
        "SELECT note_id, cita FROM nota_hallazgo WHERE person_id = ? AND verificada = 1 ORDER BY rowid", (person_id,))}
    return [{"fecha": r["note_date"], "texto": r["note_text"], "cita_comprobada": citas.get(r["note_id"])} for r in filas]


def _anotaciones(con: sqlite3.Connection, person_id: int, usadas: set) -> List[str]:
    """Líneas grises bajo el pedido (N1b, N1c, y N1a cuando la nota no basta para retirar el aviso)."""
    hoy = con.execute("SELECT hoy FROM ref").fetchone()[0]
    limite = con.execute("SELECT date(?, '-' || CAST(valor AS INTEGER) || ' months') FROM parametro "
                         "WHERE clave = 'meses_nota_realizada'", (hoy,)).fetchone()[0]
    lineas: List[str] = []
    for h in con.execute("SELECT rowid, * FROM nota_hallazgo WHERE person_id = ? AND verificada = 1 "
                         "ORDER BY note_date, note_id, prueba", (person_id,)):
        cita = f"«{h['cita']}»"
        if h["etiqueta"] == "rechazo":
            lineas.append(f"Rechazó la prueba (nota del {h['note_date']}): {cita}")
        elif h["etiqueta"] == "nefrologia":
            lineas.append(f"Seguido en Nefrología (nota del {h['note_date']}): {cita}")
        elif h["etiqueta"] == "ya_realizada" and h["note_id"] not in usadas:
            alterado = con.execute("SELECT 1 FROM nota_cac_alterado WHERE hid = ?", (h["rowid"],)).fetchone()
            por_que = (h["motivo_rechazo"] if h["motivo_rechazo"]
                       else "una nota no retira un pedido de FGe" if h["prueba"] == "FGe"   # vuelta 13, R5
                       else "resultado alterado en la nota" if alterado
                       else "sin fecha en la cita" if not h["fecha_cita"]
                       else "más de 12 meses" if h["fecha_cita"] < limite
                       else "fecha anterior al dato que dispara el aviso")
            linea = f"Nota del {h['note_date']} ({h['prueba']}, no retira el aviso: {por_que}): {cita}"
            if linea not in lineas:
                lineas.append(linea)
    return lineas


def generar(con: sqlite3.Connection) -> Dict[str, Any]:
    meta = con.execute("SELECT * FROM extract_meta").fetchone()
    hoy = date.fromisoformat(meta["fecha_referencia"])
    dias_revision = int(con.execute("SELECT valor FROM parametro WHERE clave = 'dias_revision'").fetchone()[0])
    personas = {r["person_id"]: dict(r) for r in con.execute("SELECT * FROM person")}
    # SIP sintético (si el extracto lo trae en observation): la cabecera del paciente lo enseña tal cual.
    sip = {r[0]: r[1] for r in con.execute(
        "SELECT person_id, MIN(value_as_string) FROM observation WHERE observation_source_value = 'SIP_SINTETICO' GROUP BY person_id")}
    cita_hoy = {r[0]: r[1] for r in con.execute("SELECT person_id, hora FROM cita_hoy")}
    farmaco = {r[0] for r in con.execute("SELECT person_id FROM inicio_farmaco_reciente")}
    diagnosticos: Dict[int, List[str]] = {}
    for r in con.execute(
        "SELECT person_id, grupo FROM tiene_codigo WHERE grupo IN ('DM2', 'DM1', 'HTA', 'ERC') "
        "ORDER BY person_id, CASE grupo WHEN 'DM2' THEN 1 WHEN 'DM1' THEN 2 WHEN 'HTA' THEN 3 ELSE 4 END"
    ):
        diagnosticos.setdefault(r[0], []).append(DIAGNOSTICOS[r[1]])

    por_persona: Dict[int, List[Dict[str, Any]]] = {}
    for c in con.execute("SELECT * FROM en_lista ORDER BY person_id, grupo, prioridad DESC, regla"):
        f = _fila(c)
        f["_pruebas"] = {x for x in (c["prueba"], c["prueba_extra"]) if x}
        por_persona.setdefault(c["person_id"], []).append(f)

    notas_usadas = {r[0] for r in con.execute(
        "SELECT nota_usada1 FROM candidato_motivo WHERE nota_usada1 IS NOT NULL "
        "UNION SELECT nota_usada2 FROM candidato_motivo WHERE nota_usada2 IS NOT NULL "
        "UNION SELECT note_id FROM s1c")}
    pedidos = []
    for pid, filas in por_persona.items():
        principal, *resto = filas
        # Una prueba se pide una sola vez por ficha: si el pedido principal ya la incluye, el hallazgo
        # agrupado conserva su motivo pero no repite el pedido (p. ej. S3 «FGe + CAC» con S1a/S1b «CAC»).
        pedidas = principal.pop("_pruebas")
        for t in resto:
            propias = t.pop("_pruebas")
            if t["prueba"] in pedidas:
                t["pedido"] = f"{t['prueba']} ya incluido en el pedido principal"
            pedidas |= propias
        p = personas[pid]
        aviso = None
        if pid in farmaco and principal["regla"].startswith("S3"):
            aviso = "Inicio de iSRA/iSGLT2 hace <3 meses: descenso esperable hasta 30 % (KDIGO 2024) — revisar"
        pedidos.append({
            **principal,
            "grupo_nombre": GRUPOS[principal["grupo"]],
            "person_id": pid,
            "nombre": p["person_source_value"],
            "edad": hoy.year - p["year_of_birth"],
            "sexo": SEXO.get(p["gender_concept_id"]),
            "sip": sip.get(pid),
            "diagnosticos": diagnosticos.get(pid, []),
            "hoy_en_consulta": pid in cita_hoy,
            "hora_cita": cita_hoy.get(pid),
            "aviso_farmaco": aviso,
            "fecha_revision": (hoy + timedelta(days=dias_revision)).isoformat(),
            "tambien": resto,
            "anotaciones": _anotaciones(con, pid, notas_usadas),
            "fuentes": _fuentes(con, pid),
            "evolutivos": _evolutivos(con, pid),
            "procedencia": _procedencia(con, pid),
        })
    pedidos.sort(key=lambda r: (r["grupo"], -(r["prioridad"] or 0), -r["edad"], r["person_id"]))

    fuera = [
        {**_fila(c), "person_id": c["person_id"], "nombre": personas[c["person_id"]]["person_source_value"],
         "motivo_supresion": c["motivo_supresion"], "sigue_en_lista": c["person_id"] in por_persona}
        for c in con.execute("SELECT * FROM fuera_de_la_lista ORDER BY person_id, regla")
    ]
    baseline = [r[0] for r in con.execute((RAIZ / "rules" / BASELINE).read_text(encoding="utf-8"))]
    parametros = [dict(r) for r in con.execute("SELECT * FROM parametro ORDER BY clave")]

    return {
        "etiqueta": "Maqueta · datos sintéticos",
        "fecha_referencia": meta["fecha_referencia"],
        "fuente": meta["fuente"],
        "extracto_completo": bool(meta["extracto_completo"]),
        "pacientes_revisados": con.execute("SELECT COUNT(*) FROM poblacion").fetchone()[0],
        "pacientes_extracto": len(personas),
        "pedidos": pedidos,
        "fuera_de_la_lista": fuera,
        "baseline_fge_menor_60": baseline,
        "parametros": parametros,
    }


def agregar_opciones_lector(ap: argparse.ArgumentParser) -> None:
    g = ap.add_argument_group("lector de notas (opcional; sin estas opciones no se lee ninguna nota)")
    x = g.add_mutually_exclusive_group()
    x.add_argument("--notas-grabadas", type=Path, help="JSONL con salidas ya grabadas del modelo (CI y demo)")
    x.add_argument("--lector-url", help="servidor compatible con OpenAI en la nube, p. ej. https://…  (clave en LECTOR_API_KEY)")
    g.add_argument("--lector-modelo", default="Qwen3-4B-Instruct-2507", help="nombre del modelo en ese servidor")
    g.add_argument("--grabar", type=Path, help="con --lector-url: guarda aquí las salidas (JSONL) para repetirlas después")


def crear_lector(args: argparse.Namespace) -> Optional[Callable[[str], Any]]:
    from notas.leer import LectorEndpoint, LectorGrabado
    if args.notas_grabadas:
        if not args.notas_grabadas.is_file():
            raise ValueError(f"no existe {args.notas_grabadas}")
        return LectorGrabado(args.notas_grabadas)
    if args.lector_url:
        return LectorEndpoint(args.lector_url, args.lector_modelo)
    return None


def cerrar_lector(lector: Any, args: argparse.Namespace) -> None:
    if getattr(lector, "sin_grabar", None):
        print(f"Aviso: {len(lector.sin_grabar)} notas sin salida grabada (sin efecto)", file=sys.stderr)
    if getattr(lector, "grabacion", None) is not None and args.grabar:
        args.grabar.parent.mkdir(parents=True, exist_ok=True)
        args.grabar.write_text("".join(json.dumps(g, ensure_ascii=False) + "\n" for g in lector.grabacion), encoding="utf-8")
        print(f"{len(lector.grabacion)} salidas grabadas → {args.grabar}")


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("extracto", type=Path, help="archivo .sql con el extracto (INSERTs sobre data/schema.sql), "
                                                "o un Bundle FHIR R4 en .json (lo lee fhir/leer_fhir.py)")
    ap.add_argument("--sistema-cie", action="append", default=[], help="FHIR: URI local de CIE-10-ES (se puede repetir)")
    ap.add_argument("--sistema-sip", help="FHIR: URI del identificador SIP en Patient.identifier")
    ap.add_argument("--fecha-referencia", help="FHIR: «hoy» de las reglas (por defecto, la fecha de Bundle.timestamp)")
    ap.add_argument("--completo", action="store_true",
                    help="FHIR: marcar el extracto como completo aunque el lector haya descartado algo (tras leer el informe)")
    ap.add_argument("-o", "--salida", type=Path, default=RAIZ / "ui" / "pedidos.json")
    ap.add_argument("--js-var", default="PEDIDOS", help="nombre de la variable window en el archivo .js generado (por defecto: PEDIDOS)")
    agregar_opciones_lector(ap)
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.js_var):
        ap.error("--js-var debe ser un nombre de variable JavaScript (letras, números y _)")
    if not args.extracto.is_file():
        print(f"No existe el extracto: {args.extracto}", file=sys.stderr)
        return 2
    if args.salida.suffix.lower() != ".json":
        print(f"La salida debe ser un archivo .json (junto a él se escribe el .js): {args.salida}", file=sys.stderr)
        return 2
    try:
        texto_extracto = args.extracto.read_text(encoding="utf-8")
        if args.extracto.suffix.lower() == ".json":
            from fhir.leer_fhir import bundle_a_extracto
            texto_extracto, informe = bundle_a_extracto(json.loads(texto_extracto), args.fecha_referencia,
                                                         completo=args.completo, sistemas_cie=args.sistema_cie,
                                                         sistema_sip=args.sistema_sip)
            print("FHIR: " + json.dumps({k: informe[k] for k in ("fecha_referencia", "extracto_completo",
                                                                  "completo_por_el_operador", "cargado",
                                                                  "ignorado_sin_efecto", "descartado")},
                                        ensure_ascii=False), file=sys.stderr)
        lector = crear_lector(args)
        resultado = generar(construir(texto_extracto, lector=lector))
    except (ExtractoInvalido, ValueError, RecursionError) as exc:
        print(f"No se pudo ejecutar: {exc}", file=sys.stderr)
        return 2
    cerrar_lector(lector, args)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    args.salida.write_text(texto + "\n", encoding="utf-8")
    # Copia como script para que ui/index.html se abra con doble clic (file://, sin servidor).
    args.salida.with_suffix(".js").write_text(f"window.{args.js_var} = {texto};\n", encoding="utf-8")
    print(f"{len(resultado['pedidos'])} pedidos, {len(resultado['fuera_de_la_lista'])} fuera de la lista → {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
