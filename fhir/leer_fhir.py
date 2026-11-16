"""FHIR R4 → the engine's OMOP-shaped extract (data/schema.sql). Standard library only; synthetic data only.

    python3 fhir/leer_fhir.py bundle.json -o extracto.sql [--fecha-referencia AAAA-MM-DD] [--completo]
    python3 ejecutar.py bundle.json        # ejecutar.py calls this reader for a .json input

The reader maps STRUCTURE, never meaning: it copies source codes (ICD-10, LOINC, ATC) and units as written, and the
signed rules decide what they mean (an unknown unit or code is handled there, as for any extract). It never guesses a
value or a date. What it cannot load safely it leaves out and lists in the report; if anything left out could matter to
a rule, the extract is marked INCOMPLETE (extracto_completo = 0), so the engine shows "información insuficiente"
instead of an order. The operator may override that only after reading the report (--completo). A Bundle that is not
valid FHIR in shape is refused as a whole (BundleInvalido), never half read.

FHIR R4 facts used (hl7.org/fhir/R4, read 16 Nov 2026):
- code systems: LOINC "http://loinc.org", ATC "http://www.whocc.no/atc", ICD-10 "http://hl7.org/fhir/sid/icd-10"
  (national variants have their own URI, e.g. "http://hl7.org/fhir/sid/icd-10-cm"; the spec lists none for CIE-10-ES,
  so a local URI is passed with --sistema-cie);
- Observation.status: registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown
  (only final, amended and corrected are results);
- Quantity.comparator: < | <= | >= | > ("the real value is < stated value"): a bound, not a value;
- Condition.verificationStatus: unconfirmed | provisional | differential | confirmed | refuted | entered-in-error;
- Attachment.data: base64-encoded bytes; Attachment.contentType: MIME type.
Rules added after the code review of 16 Nov (PR 16): references must name a Patient (no Group, no other type; a
"/_history/n" suffix is dropped); a partial date in the field that carries the date is never replaced by another
field; a ServiceRequest with doNotPerform is not a pending order; a paged or truncated Bundle is incomplete; a result
inside a panel component is not read; duplicate resource ids are refused; only confirmed (or unstated) diagnoses load.
Re-review: an absolute reference resolves only to the exact fullUrl of a Patient in the Bundle; a fullUrl that
contradicts its id, a non-boolean doNotPerform and a non-integer Bundle.total are refused; a rule component next to a
top-level code, and a note part that is not embedded plain text, are flagged.
Known and accepted: two final results of one test on one day are averaged by the signed rules, as for any extract;
an amended result on another day is simply the later result.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parents[1]
LOINC = "http://loinc.org"
ATC = "http://www.whocc.no/atc"
UCUM = "http://unitsofmeasure.org"
ICD10 = {"http://hl7.org/fhir/sid/icd-10"}
FECHA = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?", re.ASCII)
HORA = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", re.ASCII)
REF_PACIENTE = re.compile(r"Patient/([A-Za-z0-9\-.]{1,64})(?:/_history/[A-Za-z0-9\-.]{1,64})?", re.ASCII)
HISTORIA = re.compile(r"/_history/[A-Za-z0-9\-.]{1,64}$", re.ASCII)
CIE = re.compile(r"([A-Z])(\d{2})\.?([0-9A-Z]{0,4})", re.ASCII)
GENERO = {"male": 8507, "female": 8532}
OBS_RESULTADO = {"final", "amended", "corrected"}
CONDICION_FUERA = {"refuted", "entered-in-error"}
CONDICION_DUDOSA = {"unconfirmed", "provisional", "differential"}
CITA_VALIDA = {"booked", "arrived", "checked-in", "fulfilled"}
PARTICIPANTE_NO = {"declined"}
ENCUENTRO_VALIDO = {"planned", "arrived", "triaged", "in-progress", "finished"}
DISPENSACION_VALIDA = {"completed"}
DECLARACION_VALIDA = {"active", "completed"}
PEDIDO_VALIDO = {"active"}
INTENCION_PEDIDO = {"order", "original-order", "instance-order"}


class BundleInvalido(ValueError):
    pass


def _codigos_regla() -> Dict[str, str]:
    """LOINC code → rule group (CAC / FGE), read from the signed parameter table: one source of truth."""
    con = sqlite3.connect(":memory:")
    try:
        con.executescript((RAIZ / "data" / "schema.sql").read_text(encoding="utf-8"))
        con.executescript((RAIZ / "rules" / "00_parametros.sql").read_text(encoding="utf-8"))
        return {c: g for g, c in con.execute(
            "SELECT grupo, codigo FROM codigo_regla WHERE sistema = 'LOINC' AND grupo IN ('CAC', 'FGE')")}
    finally:
        con.close()


# -- shape helpers: a wrong JSON type is "not FHIR", refused as a whole -----------------------------------------
def _dict(v: Any, donde: str) -> Dict[str, Any]:
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise BundleInvalido(f"{donde} debe ser un objeto")
    return v


def _lista(v: Any, donde: str) -> List[Any]:
    if v is None:
        return []
    if not isinstance(v, list):
        raise BundleInvalido(f"{donde} debe ser una lista")
    return v


def _texto(v: Any, donde: str) -> Optional[str]:
    if v is None:
        return None
    if not isinstance(v, str):
        raise BundleInvalido(f"{donde} debe ser texto")
    return v


def _q(v: Any) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            raise BundleInvalido("valor no finito (NaN o infinito)")
        return repr(v)
    s = str(v)
    if "\x00" in s:
        raise BundleInvalido("texto con carácter nulo")
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        raise BundleInvalido("texto con un carácter no válido (surrogate)") from None
    return "'" + s.replace("'", "''") + "'"


def _fecha(v: Any) -> Optional[str]:
    """Full calendar date as written (time and zone dropped). Partial dates ('2015', '2015-03') are not guessed."""
    if not isinstance(v, str):
        return None
    m = FECHA.fullmatch(v)
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
    except ValueError:
        return None


def _codigos(concepto: Any, sistemas: Iterable[str], donde: str) -> List[str]:
    sistemas = set(sistemas)
    out = []
    for c in _lista(_dict(concepto, donde).get("coding"), donde + ".coding"):
        c = _dict(c, donde + ".coding[]")
        sistema, codigo = _texto(c.get("system"), "coding.system"), _texto(c.get("code"), "coding.code")
        if sistema in sistemas and codigo and codigo.strip():
            out.append(codigo.strip())
    return out


def _codigo_estado(concepto: Any, donde: str) -> Optional[str]:
    for c in _lista(_dict(concepto, donde).get("coding"), donde + ".coding"):
        codigo = _texto(_dict(c, donde).get("code"), donde + ".code")
        if codigo:
            return codigo
    return None


def _cie(codigo: str) -> str:
    """ICD-10 written without the dot ('Z992') gets it back ('Z99.2'), so the rules' prefixes match. Nothing else."""
    m = CIE.fullmatch(codigo.upper())
    if not m:
        return codigo
    return f"{m[1]}{m[2]}" + (f".{m[3]}" if m[3] else "")


def _una_eleccion(r: Dict[str, Any], prefijo: str) -> None:
    """A FHIR choice element ([x]) has one form only: two (onsetDateTime and onsetPeriod) is not valid FHIR."""
    formas = [k for k in r if k.startswith(prefijo) and k[len(prefijo):][:1].isupper()]
    if len(formas) > 1:
        raise BundleInvalido(f"{r.get('resourceType')}: varias formas de {prefijo}[x] ({', '.join(formas)})")


class Lector:
    def __init__(self, bundle: Any, sistemas_cie: Iterable[str] = (), sistema_sip: Optional[str] = None):
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            raise BundleInvalido("no es un Bundle de FHIR")
        self.bundle = bundle
        self.sistemas_cie = ICD10 | set(sistemas_cie)
        self.sistema_sip = sistema_sip
        self.loinc_regla = _codigos_regla()
        self.filas: Dict[str, List[Tuple]] = {t: [] for t in (
            "person", "observation", "condition_occurrence", "measurement", "drug_exposure", "visit_occurrence",
            "note", "pedido_pendiente")}
        self.cargado: Counter = Counter()
        self.ignorado: Counter = Counter()            # resource types or codes no rule uses: no effect
        self.descartes: List[Dict[str, str]] = []     # left out although a rule might have used it
        self.pacientes: Dict[str, int] = {}           # Patient.id → person_id
        self.urls: Dict[str, int] = {}                # entry.fullUrl → person_id
        self.inactivos: set = set()
        self.resultados: Dict[Tuple, List[Tuple[int, str, float]]] = defaultdict(list)
        self.manejadores = {
            "Condition": self._condition, "Observation": self._observation,
            "MedicationDispense": self._medicationdispense, "MedicationStatement": self._medicationstatement,
            "Appointment": self._appointment, "Encounter": self._encounter, "ServiceRequest": self._servicerequest,
            "DocumentReference": self._documentreference,
        }

    # -- helpers --------------------------------------------------------------------------------------------
    def _descartar(self, recurso: Dict[str, Any], motivo: str) -> None:
        self.descartes.append({"recurso": f"{recurso.get('resourceType')}/{recurso.get('id', '?')}", "motivo": motivo})

    def _resolver(self, ref: Any) -> Tuple[Optional[int], str]:
        """(person_id, why not). Only a reference to a Patient of this Bundle counts."""
        ref = _texto(_dict(ref, "reference").get("reference"), "reference.reference")
        if not ref:
            return None, "sin referencia"
        if ref.startswith("urn:") or "://" in ref:
            # Absolute: only the exact fullUrl of a Patient in this Bundle (a "/_history/n" suffix dropped); a Patient
            # with the same id on another server is another patient (re-review of PR 16).
            pid = self.urls.get(HISTORIA.sub("", ref))
            return (pid, "") if pid else (None, f"la referencia «{ref[:60]}» no es un Patient de este Bundle")
        m = REF_PACIENTE.fullmatch(ref)
        if not m:
            return None, f"la referencia «{ref[:60]}» no es un Patient"
        if m[1] in self.inactivos:
            return None, "inactivo"
        pid = self.pacientes.get(m[1])
        return (pid, "") if pid else (None, "no apunta a un Patient del Bundle")

    # -- bundle -----------------------------------------------------------------------------------------------
    def leer(self) -> None:
        entradas = _lista(self.bundle.get("entry"), "Bundle.entry")
        for l in _lista(self.bundle.get("link"), "Bundle.link"):
            if _texto(_dict(l, "Bundle.link[]").get("relation"), "link.relation") == "next":
                self.descartes.append({"recurso": "Bundle", "motivo": "el Bundle es una página: hay más resultados (link next)"})
        total = self.bundle.get("total")
        if total is not None and (isinstance(total, bool) or not isinstance(total, int)):
            raise BundleInvalido("Bundle.total debe ser un entero")
        if total is not None and total > len(entradas):
            self.descartes.append({"recurso": "Bundle", "motivo": f"Bundle.total {total} > {len(entradas)} entradas"})
        recursos, vistos = [], set()
        for e in entradas:
            e = _dict(e, "Bundle.entry[]")
            r = _dict(e.get("resource"), "entry.resource")
            t = _texto(r.get("resourceType"), "resourceType")
            if not t:
                raise BundleInvalido("una entrada del Bundle no tiene recurso")
            clave = (t, r.get("id"))
            if r.get("id") is not None:
                if clave in vistos:
                    raise BundleInvalido(f"recurso repetido: {t}/{r.get('id')}")
                vistos.add(clave)
            if t == "OperationOutcome" or _texto(_dict(e.get("search"), "entry.search").get("mode"), "search.mode") == "outcome":
                self.descartes.append({"recurso": f"{t}/{r.get('id', '?')}", "motivo": "el servidor informó de un problema (OperationOutcome)"})
                continue
            recursos.append((e, r))
        for e, r in recursos:                                    # patients first: every other resource points to one
            if r["resourceType"] == "Patient":
                self._patient(e, r)
        if not self.pacientes:
            raise BundleInvalido("el Bundle no tiene ningún Patient activo")
        for _, r in recursos:
            t = r["resourceType"]
            if t == "Patient":
                continue
            metodo = self.manejadores.get(t)
            if metodo is None:
                self.ignorado[t] += 1
                continue
            metodo(r)
        self._resultados_corregidos()

    def _sujeto(self, r: Dict[str, Any]) -> Optional[int]:
        pid, porque = self._resolver(r.get("subject"))
        if pid is None:
            if porque == "inactivo":
                self.ignorado[f"{r['resourceType']} de un Patient inactivo"] += 1
            else:
                self._descartar(r, porque)
        return pid

    def _patient(self, e: Dict[str, Any], r: Dict[str, Any]) -> None:
        rid = _texto(r.get("id"), "Patient.id")
        url = _texto(e.get("fullUrl"), "entry.fullUrl")
        if r.get("active") is False:
            if rid:
                self.inactivos.add(rid)
            self.ignorado["Patient inactivo"] += 1
            return
        nacimiento = _texto(r.get("birthDate"), "Patient.birthDate")
        if not (nacimiento and re.match(r"\d{4}(-\d{2}(-\d{2})?)?$", nacimiento, re.ASCII)):
            self._descartar(r, "sin año de nacimiento")
            return
        if not rid and not url:
            self._descartar(r, "Patient sin id ni fullUrl")
            return
        pid = len(self.filas["person"]) + 1
        if rid:
            if rid in self.pacientes:
                raise BundleInvalido(f"dos Patient con el mismo id: {rid}")
            self.pacientes[rid] = pid
        if url and REF_PACIENTE.fullmatch(url) and REF_PACIENTE.fullmatch(url)[1] != rid:
            raise BundleInvalido(f"Patient con fullUrl «{url}» que no coincide con su id «{rid}»")
        if url:
            if url in self.urls:
                raise BundleInvalido(f"dos Patient con el mismo fullUrl: {url}")
            self.urls[url] = pid
        nombre = None
        for n in _lista(r.get("name"), "Patient.name"):
            n = _dict(n, "Patient.name[]")
            nombre = _texto(n.get("text"), "name.text") or next(
                (g for g in _lista(n.get("given"), "name.given") if isinstance(g, str)), None)
            if nombre:
                break
        genero = _texto(r.get("gender"), "Patient.gender")
        self.filas["person"].append((pid, GENERO.get(genero, 0), int(nacimiento[:4]), 0, 0, nombre,
                                     {"male": "H", "female": "M"}.get(genero)))
        for i in _lista(r.get("identifier"), "Patient.identifier"):
            i = _dict(i, "Patient.identifier[]")
            if self.sistema_sip and i.get("system") == self.sistema_sip and isinstance(i.get("value"), str):
                self.filas["observation"].append((len(self.filas["observation"]) + 1, pid, 0, "1900-01-01", 0,
                                                  i["value"], "SIP_SINTETICO"))
                break
        self.cargado["Patient"] += 1

    def _condition(self, r: Dict[str, Any]) -> None:
        pid = self._sujeto(r)
        if pid is None:
            return
        estado = _codigo_estado(r.get("verificationStatus"), "Condition.verificationStatus")
        if estado in CONDICION_FUERA:
            self.ignorado["Condition refutada o errónea"] += 1
            return
        if estado in CONDICION_DUDOSA:
            self._descartar(r, f"diagnóstico no confirmado ({estado})")
            return
        codigos = [_cie(c) for c in _codigos(r.get("code"), self.sistemas_cie, "Condition.code")]
        if not codigos:
            self._descartar(r, "sin código CIE-10 (sistema no reconocido: use --sistema-cie)")
            return
        _una_eleccion(r, "onset")
        if "onsetDateTime" in r:
            inicio = _fecha(r["onsetDateTime"])
        elif "onsetPeriod" in r:
            inicio = _fecha(_dict(r["onsetPeriod"], "onsetPeriod").get("start"))
        elif any(k.startswith("onset") for k in r):
            inicio = None                                     # onsetAge, onsetString…: not a date
        else:
            inicio = None
        if not inicio:
            self._descartar(r, "sin fecha completa de inicio (onset); la fecha de registro no es el inicio")
            return
        for c in dict.fromkeys(codigos):          # every ICD-10 coding: an exclusion code may be the second one
            self.filas["condition_occurrence"].append((len(self.filas["condition_occurrence"]) + 1, pid, 0, inicio, 0, c))
        self.cargado["Condition"] += 1

    def _observation(self, r: Dict[str, Any]) -> None:
        codigos = _codigos(r.get("code"), {LOINC}, "Observation.code")
        codigo = next((c for c in codigos if c in self.loinc_regla), None)
        en_componente = any(c in self.loinc_regla for comp in _lista(r.get("component"), "Observation.component")
                            for c in _codigos(_dict(comp, "component[]").get("code"), {LOINC}, "component.code"))
        if codigo is None and not en_componente:
            self.ignorado["Observation que no usa ninguna regla"] += 1
            return
        pid = self._sujeto(r)
        if pid is None:
            return
        estado = _texto(r.get("status"), "Observation.status")
        if estado not in OBS_RESULTADO:
            self.ignorado[f"Observation {estado} (no es un resultado)"] += 1
            return
        if en_componente:
            # A rule result inside a panel component is never read, with or without a top-level code: flagged.
            self._descartar(r, "resultado dentro de un componente de panel: no se lee")
            if codigo is None:
                return
        _una_eleccion(r, "effective")
        _una_eleccion(r, "value")
        if "effectiveDateTime" in r:
            fecha = _fecha(r["effectiveDateTime"])
        elif "effectivePeriod" in r:
            fecha = _fecha(_dict(r["effectivePeriod"], "effectivePeriod").get("start"))
        else:
            fecha = None                                      # 'issued' is when it was reported, not when it was done
        if not fecha:
            self._descartar(r, "resultado sin fecha completa (effective)")
            return
        q = r.get("valueQuantity")
        if q is None and "dataAbsentReason" in r:
            if _codigo_estado(r.get("dataAbsentReason"), "dataAbsentReason") == "unknown":
                # The test was done and its value is unknown: loaded with an empty value, as the synthetic blind set
                # has it; the signed rules already handle "CAC with no value".
                self.filas["measurement"].append((len(self.filas["measurement"]) + 1, pid, 0, fecha, 0, None, None, codigo))
                self.cargado["Observation sin valor (dataAbsentReason unknown)"] += 1
            else:
                self.ignorado["Observation no realizada o con error (dataAbsentReason)"] += 1
            return
        q = _dict(q, "valueQuantity")
        valor = q.get("value")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            self._descartar(r, "resultado sin valueQuantity numérico")
            return
        try:
            valor = float(valor)
        except OverflowError:
            raise BundleInvalido("valor numérico fuera de rango") from None
        if q.get("comparator"):
            self._descartar(r, f"resultado con comparador «{q['comparator']}»: es un límite, no un valor")
            return
        unidad = q.get("code") if q.get("system") == UCUM and q.get("code") else q.get("unit")
        unidad = _texto(unidad, "valueQuantity.unit")
        self.resultados[(pid, codigo, fecha)].append((len(self.filas["measurement"]), estado, valor))
        self.filas["measurement"].append((len(self.filas["measurement"]) + 1, pid, 0, fecha, 0, valor, unidad, codigo))
        self.cargado["Observation"] += 1

    def _resultados_corregidos(self) -> None:
        """Same patient, test and day, one of them amended or corrected, different values: which one stands is not
        knowable here (the rules would average them). Both are left out and the extract marked incomplete."""
        quitar = set()
        for (pid, codigo, fecha), filas in self.resultados.items():
            if len(filas) > 1 and any(e in ("amended", "corrected") for _, e, _ in filas) and len({v for *_, v in filas}) > 1:
                quitar |= {i for i, _, _ in filas}
                self.descartes.append({"recurso": f"Observation {codigo} {fecha}",
                                       "motivo": "resultado corregido junto a otro del mismo día con otro valor"})
        if quitar:
            filas = [f for i, f in enumerate(self.filas["measurement"]) if i not in quitar]
            self.filas["measurement"] = [(n + 1, *f[1:]) for n, f in enumerate(filas)]
            self.cargado["Observation"] -= len(quitar)

    def _medicacion(self, r: Dict[str, Any], inicio: Optional[str], fin: Optional[str]) -> None:
        codigos = _codigos(r.get("medicationCodeableConcept"), {ATC}, "medicationCodeableConcept")
        if not codigos:
            self.ignorado[f"{r['resourceType']} sin código ATC (solo afecta a la marca «inicio reciente»)"] += 1
            return
        pid = self._sujeto(r)
        if pid is None:
            return
        if not inicio:
            self._descartar(r, "medicamento sin fecha completa")
            return
        self.filas["drug_exposure"].append((len(self.filas["drug_exposure"]) + 1, pid, 0, inicio, fin or inicio, 0, codigos[0]))
        self.cargado[r["resourceType"]] += 1

    def _medicationdispense(self, r: Dict[str, Any]) -> None:
        estado = _texto(r.get("status"), "status")
        if estado not in DISPENSACION_VALIDA:
            self.ignorado[f"MedicationDispense {estado}"] += 1
            return
        self._medicacion(r, _fecha(r.get("whenHandedOver")), None)

    def _medicationstatement(self, r: Dict[str, Any]) -> None:
        estado = _texto(r.get("status"), "status")
        if estado not in DECLARACION_VALIDA:
            self.ignorado[f"MedicationStatement {estado}"] += 1
            return
        periodo = _dict(r.get("effectivePeriod"), "effectivePeriod")
        inicio = _fecha(r["effectiveDateTime"]) if "effectiveDateTime" in r else _fecha(periodo.get("start"))
        self._medicacion(r, inicio, _fecha(periodo.get("end")))

    def _appointment(self, r: Dict[str, Any]) -> None:
        estado = _texto(r.get("status"), "status")
        if estado not in CITA_VALIDA:
            self.ignorado[f"Appointment {estado}"] += 1
            return
        pids = []
        for p in _lista(r.get("participant"), "Appointment.participant"):
            p = _dict(p, "participant[]")
            if _texto(p.get("status"), "participant.status") in PARTICIPANTE_NO:
                continue
            pid, _ = self._resolver(p.get("actor"))
            if pid:
                pids.append(pid)
        if len(set(pids)) != 1:
            self._descartar(r, "cita sin un único Patient del Bundle que acepte")
            return
        self._visita(r, pids[0], r.get("start"))

    def _encounter(self, r: Dict[str, Any]) -> None:
        estado = _texto(r.get("status"), "status")
        if estado not in ENCUENTRO_VALIDO:
            self.ignorado[f"Encounter {estado}"] += 1
            return
        pid = self._sujeto(r)
        if pid is not None:
            self._visita(r, pid, _dict(r.get("period"), "Encounter.period").get("start"))

    def _visita(self, r: Dict[str, Any], pid: int, inicio: Any) -> None:
        fecha = _fecha(inicio)
        if not fecha:
            self._descartar(r, "cita o encuentro sin fecha completa")
            return
        hora = inicio[:16] if HORA.match(inicio) else None
        self.filas["visit_occurrence"].append((len(self.filas["visit_occurrence"]) + 1, pid, 0, fecha, fecha, 0, hora))
        self.cargado[r["resourceType"]] += 1

    def _servicerequest(self, r: Dict[str, Any]) -> None:
        codigo = next((c for c in _codigos(r.get("code"), {LOINC}, "ServiceRequest.code") if c in self.loinc_regla), None)
        if codigo is None:
            self.ignorado["ServiceRequest de otra prueba"] += 1
            return
        pid = self._sujeto(r)
        if pid is None:
            return
        if "doNotPerform" in r and not isinstance(r["doNotPerform"], bool):
            raise BundleInvalido("ServiceRequest.doNotPerform debe ser true o false")
        if r.get("doNotPerform") is True:
            self._descartar(r, "ServiceRequest con doNotPerform: no es un pedido pendiente")
            return
        estado, intencion = _texto(r.get("status"), "status"), _texto(r.get("intent"), "intent")
        if estado not in PEDIDO_VALIDO or intencion not in INTENCION_PEDIDO:
            self.ignorado[f"ServiceRequest {estado}/{intencion}"] += 1
            return
        fecha = _fecha(r.get("authoredOn"))
        if not fecha:
            self._descartar(r, "pedido sin fecha completa")
            return
        prueba = {"CAC": "CAC", "FGE": "FGe"}[self.loinc_regla[codigo]]
        self.filas["pedido_pendiente"].append((len(self.filas["pedido_pendiente"]) + 1, pid, prueba, fecha))
        self.cargado["ServiceRequest"] += 1

    def _documentreference(self, r: Dict[str, Any]) -> None:
        if _texto(r.get("status"), "status") != "current" or r.get("docStatus") == "entered-in-error":
            self.ignorado[f"DocumentReference {r.get('status')}"] += 1
            return
        pid = self._sujeto(r)
        if pid is None:
            return
        fecha = _fecha(r.get("date"))
        textos, otros = [], 0
        for c in _lista(r.get("content"), "DocumentReference.content"):
            a = _dict(_dict(c, "content[]").get("attachment"), "content.attachment")
            tipo = (_texto(a.get("contentType"), "contentType") or "").split(";")[0].strip()
            if not (tipo == "text/plain" and isinstance(a.get("data"), str)):
                otros += 1
                continue
            try:
                textos.append(base64.b64decode(a["data"], validate=True).decode("utf-8"))
            except (binascii.Error, UnicodeDecodeError):
                self._descartar(r, "texto de la nota no es base64 UTF-8")
                return
        if not textos:
            self._descartar(r, "nota sin texto plano incrustado (text/plain en attachment.data)")
            return
        if otros:
            self._descartar(r, f"{otros} parte(s) de la nota no son texto plano incrustado: no se leen")
        if not fecha:
            self._descartar(r, "nota sin fecha completa")
            return
        self.filas["note"].append((len(self.filas["note"]) + 1, pid, fecha, 0, 0, _texto(r.get("description"), "description"),
                                   "\n".join(textos), 0, 0))
        self.cargado["DocumentReference"] += 1


COLUMNAS = {
    "person": "person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, person_source_value, gender_source_value",
    "observation": "observation_id, person_id, observation_concept_id, observation_date, observation_type_concept_id, value_as_string, observation_source_value",
    "condition_occurrence": "condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value",
    "measurement": "measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value",
    "drug_exposure": "drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, drug_source_value",
    "visit_occurrence": "visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id, visit_start_datetime",
    "note": "note_id, person_id, note_date, note_type_concept_id, note_class_concept_id, note_title, note_text, encoding_concept_id, language_concept_id",
    "pedido_pendiente": "pedido_id, person_id, prueba, fecha_pedido",
}


def bundle_a_extracto(bundle: Any, fecha_referencia: Optional[str] = None, completo: bool = False,
                      sistemas_cie: Iterable[str] = (), sistema_sip: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Returns (extract SQL, report). completo=True is the operator's override after reading the report."""
    try:
        lector = Lector(bundle, sistemas_cie, sistema_sip)
        lector.leer()
    except (TypeError, AttributeError, KeyError, OverflowError, RecursionError) as exc:
        raise BundleInvalido(f"el Bundle no tiene la forma de FHIR R4 ({type(exc).__name__})") from None
    hoy = fecha_referencia or _fecha(bundle.get("timestamp"))
    if not hoy or _fecha(hoy) != hoy:
        raise BundleInvalido("falta la fecha de referencia (--fecha-referencia o Bundle.timestamp)")
    marcado_completo = bool(completo) or not lector.descartes
    sql = ["-- Extracto generado por fhir/leer_fhir.py a partir de un Bundle FHIR R4. Solo datos sintéticos.",
           f"INSERT INTO extract_meta VALUES (1, {_q(hoy)}, {int(marcado_completo)}, 'fhir_r4');"]
    for tabla, filas in lector.filas.items():
        for f in filas:
            sql.append(f"INSERT INTO {tabla} ({COLUMNAS[tabla]}) VALUES ({', '.join(_q(v) for v in f)});")
    informe = {"fecha_referencia": hoy, "extracto_completo": marcado_completo,
               "completo_por_el_operador": bool(completo) and bool(lector.descartes),
               "cargado": dict(sorted(lector.cargado.items())), "ignorado_sin_efecto": dict(sorted(lector.ignorado.items())),
               "descartado": lector.descartes,
               "pacientes": dict(sorted(lector.pacientes.items(), key=lambda kv: kv[1]))}
    return "\n".join(sql) + "\n", informe


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="FHIR R4 Bundle → extracto del motor (data/schema.sql)")
    ap.add_argument("bundle", type=Path)
    ap.add_argument("-o", "--salida", type=Path, help="archivo .sql (por defecto, a la salida estándar)")
    ap.add_argument("--fecha-referencia", help="«hoy» de las reglas (por defecto, la fecha de Bundle.timestamp)")
    ap.add_argument("--completo", action="store_true",
                    help="marcar el extracto como completo aunque se haya descartado algo (solo tras leer el informe)")
    ap.add_argument("--sistema-cie", action="append", default=[], help="URI local de CIE-10-ES (se puede repetir)")
    ap.add_argument("--sistema-sip", help="URI del identificador SIP en Patient.identifier")
    args = ap.parse_args(argv)
    try:
        sql, informe = bundle_a_extracto(json.loads(args.bundle.read_text(encoding="utf-8")), args.fecha_referencia,
                                         args.completo, args.sistema_cie, args.sistema_sip)
        if args.salida:
            args.salida.write_text(sql, encoding="utf-8")
        else:
            sys.stdout.write(sql)
    except (ValueError, OSError, RecursionError) as exc:      # BundleInvalido and json errors are ValueErrors
        print(f"No se pudo leer el Bundle: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(informe, ensure_ascii=False, indent=1), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
