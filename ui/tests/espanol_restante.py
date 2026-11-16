"""List Spanish words left in English mode (outside «note quotes» and lang="es" notes).

    node ui/tests/recoger_textos.mjs en > textos_en.json && python3 ui/tests/espanol_restante.py textos_en.json

«…» is reserved for text quoted from a clinical note (interface text uses “…”), so it is skipped, except for the
rule's own placeholder words listed in QUOTED_UI. Patient names are removed as whole names; only the code
identifiers in CODE are skipped.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Words that only occur in Spanish interface text (English look-alikes excluded), plus Spanish clinical acronyms.
ES = set("""de del el la los las sin con para por que una uno unos unas en y se ya hoy meses años días pedido pedidos
nota notas paciente pacientes firmar firmado aplazar aplazado descartar descartado prueba pruebas solicitar
solicitado solicita último última cribado cupo regla reglas extracto historia consulta valorar repetir según cita
comprobada informe mutua analítica orina función renal descenso caída cambio hallazgo motivo decisión registro aún
hay está están son cada nunca también otro otra fecha hora resultado resultados pendiente pendientes vigente ninguno
ninguna lista fuera dónde sale cuando debe deja queda falta tu tú su sus más menos tras sobre como cómo qué porque
codificada codificar diagnóstico diagnósticos fármaco retirado retirada rechazó rechazo hace desde hasta entre
aviso alerta sí nuevo nueva primera ver abrir cerrar volver dm2 hta ieca ara isra isglt2 erc fge cac""".split())
QUOTED_UI = {"vacía"}
CODE = {"condition_occurrence", "measurement", "drug_exposure", "observation", "pedido_pendiente", "note",
        "visit_occurrence", "extract_meta", "nota_hallazgo", "notas/verificar.py",
        "PROT-AP ERC"}                                    # proper name of the Valencian protocol (cited as is)
ACCENT = re.compile(r"[áéíóúñ¿¡]")

names = {"Carmen López"}                              # the fictional doctor
for f in ("pedidos.json", "pedidos_aguja.json", "pedidos_cupo.json"):
    d = json.load(open(ROOT / "ui" / f))
    for p in d["pedidos"] + d["fuera_de_la_lista"]:
        if p.get("nombre"):
            names.add(p["nombre"])
NAME_RE = re.compile("|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)), re.IGNORECASE)

data = json.load(open(sys.argv[1]))
assert not data["errores"], data["errores"]
bad = {}
for text, where in data["textos"].items():
    quoted = {w.lower() for q in re.findall(r"«([^»]*)»", text) for w in re.findall(r"\w+", q)}
    plain = re.sub(r"«[^»]*»", " ", text)
    plain = NAME_RE.sub(" ", plain)
    for c in CODE:
        plain = plain.replace(c, " ")
    words = {w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ0-9]+", plain) if len(w) > 1}
    hits = sorted((words & ES) | {w for w in words if ACCENT.search(w)} | (quoted & QUOTED_UI))
    if hits:
        bad[text] = (hits, where)
for t, (h, w) in sorted(bad.items())[:300]:
    print(f"{','.join(h):30.30} | {t[:170]}  [{w}]")
print(f"\n{len(bad)} texts with Spanish words")
sys.exit(1 if bad else 0)
