"""FHIR R4 reader (fhir/leer_fhir.py): round trip on every synthetic set, and the cases it must not load."""
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ejecutar  # noqa: E402
from fhir.extracto_a_fhir import SISTEMA_CIE, SISTEMA_SIP, extracto_a_bundle  # noqa: E402
from fhir.leer_fhir import BundleInvalido, bundle_a_extracto  # noqa: E402
from notas.leer import LectorGrabado  # noqa: E402

SETS = {
    "demo": "data/synthetic/demo_seed.sql",
    "ciego": "data/synthetic/ciego/extracto.sql",
    "notas_dev": "data/synthetic/notas_dev/extracto.sql",
    "aguja": "data/synthetic/aguja/extracto.sql",
    "cupo_250": "data/synthetic/cupo_250.sql",
    "cupo_espanol_1000": "data/synthetic/cupo_espanol_1000/extracto.sql",
}
CIE = [SISTEMA_CIE]


def _normal(salida, nuevo_a_viejo=None):
    """Engine output without the source tag; person ids mapped back to the original extract's."""
    out = json.loads(json.dumps(salida))
    out.pop("fuente", None)
    for lista in ("pedidos", "fuera_de_la_lista"):
        for p in out.get(lista, []):
            if nuevo_a_viejo:
                viejo = nuevo_a_viejo[p["person_id"]]
                p["id"] = re.sub(rf"-{p['person_id']}-", f"-{viejo}-", p["id"], count=1)
                p["person_id"] = viejo
        out[lista] = sorted(out.get(lista, []), key=lambda p: p["id"])
    return out


def _ida_y_vuelta(sql, lector=None, lector2=None):
    original = ejecutar.generar(ejecutar.construir(sql, lector=lector))
    sql2, informe = bundle_a_extracto(extracto_a_bundle(sql), sistemas_cie=CIE, sistema_sip=SISTEMA_SIP)
    vuelta = ejecutar.generar(ejecutar.construir(sql2, lector=lector2))
    mapa = {v: int(k.split("-")[1]) for k, v in informe["pacientes"].items()}
    return _normal(original), _normal(vuelta, mapa), informe


@pytest.mark.parametrize("nombre", sorted(SETS))
def test_round_trip_gives_the_same_orders(nombre):
    original, vuelta, informe = _ida_y_vuelta((ROOT / SETS[nombre]).read_text(encoding="utf-8"))
    assert informe["descartado"] == [] and informe["extracto_completo"] is True
    assert vuelta == original


@pytest.mark.parametrize("conjunto,grabacion", [
    ("notas_dev", "salidas_oraculo.jsonl"), ("notas_dev", "salidas_qwen3-4b-instruct-2507.jsonl"),
    ("aguja", "salidas_oraculo.jsonl"), ("aguja", "salidas_qwen3-4b-instruct-2507.jsonl"),
])
def test_round_trip_with_the_note_reader(conjunto, grabacion):
    """Note text survives base64 byte for byte, so the recorded model outputs (keyed by the text's hash) replay."""
    g = ROOT / "data/synthetic" / conjunto / grabacion
    original, vuelta, _ = _ida_y_vuelta((ROOT / SETS[conjunto]).read_text(encoding="utf-8"),
                                        LectorGrabado(g), LectorGrabado(g))
    assert vuelta == original


@pytest.mark.parametrize("nombre,origen", [("demo", "demo"), ("aguja", "aguja")])
def test_committed_bundles_are_current(nombre, origen):
    b = extracto_a_bundle((ROOT / SETS[origen]).read_text(encoding="utf-8"))
    assert json.loads((ROOT / f"data/synthetic/fhir/{nombre}_bundle.json").read_text(encoding="utf-8")) == b


def test_engine_reads_a_bundle_from_the_command_line(tmp_path):
    out = tmp_path / "p.json"
    r = subprocess.run([sys.executable, "ejecutar.py", "data/synthetic/fhir/demo_bundle.json", "--sistema-cie", SISTEMA_CIE,
                        "--sistema-sip", SISTEMA_SIP, "-o", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    fhir = json.loads(out.read_text(encoding="utf-8"))
    demo = ejecutar.generar(ejecutar.construir((ROOT / SETS["demo"]).read_text(encoding="utf-8")))
    assert fhir["fuente"] == "fhir_r4" and _normal(fhir) == _normal(demo)


# -- what the reader must not load ---------------------------------------------------------------------------
def _bundle(*recursos, timestamp="2026-11-14T00:00:00+01:00"):
    pac = {"resourceType": "Patient", "id": "p1", "birthDate": "1960", "gender": "female", "name": [{"text": "Ana"}]}
    return {"resourceType": "Bundle", "type": "collection", "timestamp": timestamp,
            "entry": [{"resource": pac}] + [{"resource": r} for r in recursos]}


def _obs(**kw):
    r = {"resourceType": "Observation", "id": "o1", "status": "final", "subject": {"reference": "Patient/p1"},
         "effectiveDateTime": "2026-05-01", "code": {"coding": [{"system": "http://loinc.org", "code": "9318-7"}]},
         "valueQuantity": {"value": 12, "unit": "mg/g"}}
    r.update(kw)
    return r


def _cond(**kw):
    r = {"resourceType": "Condition", "id": "c1", "subject": {"reference": "Patient/p1"}, "onsetDateTime": "2015-01-01",
         "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9"}]}}
    r.update(kw)
    return r


def _leer(*recursos, **kw):
    sql, informe = bundle_a_extracto(_bundle(*recursos), **kw)
    return sql, informe


def test_a_clean_bundle_loads_and_is_complete():
    sql, inf = _leer(_cond(), _obs())
    assert inf["extracto_completo"] and inf["cargado"] == {"Condition": 1, "Observation": 1, "Patient": 1}
    assert "'9318-7'" in sql and "'E11.9'" in sql and " 12.0, 'mg/g'" in sql


@pytest.mark.parametrize("recurso,motivo", [
    (_obs(valueQuantity={"value": 30, "comparator": "<", "unit": "mg/g"}), "comparador"),
    (_obs(valueQuantity={"value": "12", "unit": "mg/g"}), "valueQuantity"),
    (_obs(valueQuantity={"value": True, "unit": "mg/g"}), "valueQuantity"),
    (_obs(effectiveDateTime="2026-05"), "fecha"),
    (_obs(subject={"reference": "Patient/otro"}), "Patient"),
    (_cond(code={"coding": [{"system": "http://snomed.info/sct", "code": "44054006"}]}), "CIE-10"),
    (_cond(onsetDateTime="2015"), "fecha"),
    ({"resourceType": "DocumentReference", "id": "d1", "status": "current", "subject": {"reference": "Patient/p1"},
      "date": "2026-10-01T00:00:00Z", "content": [{"attachment": {"contentType": "text/plain", "data": "@@no-b64@@"}}]}, "base64"),
    ({"resourceType": "DocumentReference", "id": "d2", "status": "current", "subject": {"reference": "Patient/p1"},
      "date": "2026-10-01T00:00:00Z", "content": [{"attachment": {"contentType": "application/pdf", "url": "x.pdf"}}]}, "texto plano"),
    # code review of PR 16, H1-H7
    (_obs(subject={"reference": "Group/p1"}), "no es un Patient"),
    (_obs(effectiveDateTime="2024-05", issued="2026-10-20T10:00:00Z"), "fecha"),      # H2: issued is not a fallback
    (_cond(onsetDateTime="2005", recordedDate="2026-11-01"), "fecha"),                 # H2: recordedDate is not an onset
    (_cond(onsetDateTime=None), "fecha"),
    ({"resourceType": "ServiceRequest", "id": "s1", "status": "active", "intent": "order", "doNotPerform": True,
      "subject": {"reference": "Patient/p1"}, "authoredOn": "2026-11-01",
      "code": {"coding": [{"system": "http://loinc.org", "code": "9318-7"}]}}, "doNotPerform"),          # H3
    ({"resourceType": "Observation", "id": "o9", "status": "final", "subject": {"reference": "Patient/p1"},
      "effectiveDateTime": "2026-05-01", "code": {"coding": [{"system": "http://loinc.org", "code": "24362-6"}]},
      "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "9318-7"}]},
                     "valueQuantity": {"value": 12, "unit": "mg/g"}}]}, "componente"),                # H5
    (_cond(verificationStatus={"coding": [{"code": "provisional"}]}), "no confirmado"),               # H7
    (_cond(verificationStatus={"coding": [{"code": "differential"}]}), "no confirmado"),
    ({"resourceType": "OperationOutcome", "id": "oo", "issue": [{"severity": "warning", "code": "too-costly"}]}, "problema"),
])
def test_anything_left_out_that_a_rule_could_use_marks_the_extract_incomplete(recurso, motivo):
    _, inf = _leer(recurso)
    assert not inf["extracto_completo"] and len(inf["descartado"]) == 1 and motivo in inf["descartado"][0]["motivo"]
    _, inf2 = _leer(recurso, completo=True)           # the operator's override, after reading the report
    assert inf2["extracto_completo"] and inf2["completo_por_el_operador"]


@pytest.mark.parametrize("recurso", [
    _obs(status="preliminary"), _obs(status="entered-in-error"), _obs(status="cancelled"),
    _obs(code={"coding": [{"system": "http://loinc.org", "code": "2160-0"}]}),     # serum creatinine: no rule uses it
    _obs(code={"coding": [{"system": "http://local/lab", "code": "ACR"}]}),        # no LOINC: no rule reads it (as in SQL)
    _obs(valueQuantity=None, dataAbsentReason={"coding": [{"code": "not-performed"}]}),   # M1: not done
    {"resourceType": "MedicationStatement", "id": "m1", "status": "active", "subject": {"reference": "Patient/p1"},
     "medicationCodeableConcept": {"text": "empagliflozina"}, "effectiveDateTime": "2026-09-01"},
    _cond(verificationStatus={"coding": [{"code": "refuted"}]}),
    _cond(verificationStatus={"coding": [{"code": "entered-in-error"}]}),
    {"resourceType": "AllergyIntolerance", "id": "a1", "patient": {"reference": "Patient/p1"}},
    {"resourceType": "ServiceRequest", "id": "s1", "status": "completed", "intent": "order", "subject": {"reference": "Patient/p1"},
     "authoredOn": "2026-11-01", "code": {"coding": [{"system": "http://loinc.org", "code": "9318-7"}]}},
])
def test_what_no_rule_uses_is_ignored_without_effect(recurso):
    sql, inf = _leer(recurso)
    assert inf["extracto_completo"] and inf["descartado"] == [] and sum(inf["ignorado_sin_efecto"].values()) == 1
    assert "INSERT INTO measurement" not in sql and "INSERT INTO condition_occurrence" not in sql


def test_a_result_with_no_value_is_loaded_empty_as_in_omop():
    sql, inf = _leer(_obs(valueQuantity=None, dataAbsentReason={"coding": [{"code": "unknown"}]}))
    assert inf["extracto_completo"] and "NULL, NULL, '9318-7'" in sql


def test_ucum_code_is_preferred_and_units_are_passed_through_for_the_rules():
    sql, _ = _leer(_obs(code={"coding": [{"system": "http://loinc.org", "code": "62238-1"}]},
                        valueQuantity={"value": 55, "unit": "mL/min/1.73m2", "system": "http://unitsofmeasure.org",
                                       "code": "mL/min/{1.73_m2}"}))
    assert "'mL/min/{1.73_m2}'" in sql


def test_text_cannot_break_out_of_the_sql():
    nombre = "O'Brien'); DROP TABLE person; --"
    b = _bundle(_cond())
    b["entry"][0]["resource"]["name"] = [{"text": nombre}]
    sql, _ = bundle_a_extracto(b)
    con = ejecutar.construir(sql)
    assert con.execute("SELECT person_source_value FROM person").fetchone()[0] == nombre


def test_a_note_survives_byte_for_byte():
    texto = "CAC 45 mg/g el 15/09/2026 · «trae informe» ñ"
    doc = {"resourceType": "DocumentReference", "id": "d1", "status": "current", "subject": {"reference": "Patient/p1"},
           "date": "2026-10-01T09:00:00+02:00", "description": "Evolutivo",
           "content": [{"attachment": {"contentType": "text/plain; charset=utf-8",
                                       "data": base64.b64encode(texto.encode()).decode()}}]}
    con = ejecutar.construir(_leer(doc)[0])
    assert tuple(con.execute("SELECT note_text, note_date FROM note").fetchone()) == (texto, "2026-10-01")


@pytest.mark.parametrize("bundle,error", [
    ({"resourceType": "Patient"}, "Bundle"),
    ({"resourceType": "Bundle", "entry": [{"resource": {"resourceType": "Patient", "id": "a", "birthDate": "1950"}},
                                          {"resource": {"resourceType": "Patient", "id": "a", "birthDate": "1951"}}]}, "repetido"),
    (_bundle(_obs(), _obs()), "repetido"),                                                         # H6: same id twice
    ({"resourceType": "Bundle", "timestamp": "2026-11-14", "entry": []}, "ningún Patient"),       # H4
    (_bundle(timestamp=None), "fecha de referencia"),
])
def test_invalid_bundles_are_refused(bundle, error):
    with pytest.raises(BundleInvalido, match=error):
        bundle_a_extracto(bundle)


def test_non_finite_numbers_are_refused():
    with pytest.raises(BundleInvalido, match="no finito"):
        bundle_a_extracto(json.loads(json.dumps(_bundle(_obs(valueQuantity={"value": float("nan"), "unit": "mg/g"})))))


def test_every_icd10_coding_of_a_condition_is_loaded():
    sql, _ = _leer(_cond(code={"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "N18.5"},
                                          {"system": "http://hl7.org/fhir/sid/icd-10", "code": "Z99.2"}]}))
    assert "'N18.5'" in sql and "'Z99.2'" in sql


def _row_people(sql):
    con = ejecutar.construir(sql)
    return {r[0] for r in con.execute("SELECT DISTINCT person_id FROM measurement")}


def test_h1_history_and_other_types_never_reach_another_patient():
    b = _bundle(_obs(subject={"reference": "Patient/p1/_history/3"}))
    b["entry"].append({"resource": {"resourceType": "Patient", "id": "3", "birthDate": "1950"}})
    sql, inf = bundle_a_extracto(b)
    assert inf["extracto_completo"] and _row_people(sql) == {inf["pacientes"]["p1"]}


def test_h4_a_paged_or_truncated_bundle_is_incomplete():
    b = _bundle(_obs())
    b["link"] = [{"relation": "next", "url": "https://x/fhir/Observation?page=2"}]
    assert not bundle_a_extracto(b)[1]["extracto_completo"]
    b = _bundle(_obs())
    b["total"] = 5
    assert not bundle_a_extracto(b)[1]["extracto_completo"]


def test_h6_a_corrected_result_next_to_the_original_is_left_out():
    a = _obs(id="o1", code={"coding": [{"system": "http://loinc.org", "code": "62238-1"}]},
             valueQuantity={"value": 80, "unit": "mL/min/1.73m2"})
    b = _obs(id="o2", status="corrected", code={"coding": [{"system": "http://loinc.org", "code": "62238-1"}]},
             valueQuantity={"value": 40, "unit": "mL/min/1.73m2"})
    sql, inf = _leer(a, b)
    assert not inf["extracto_completo"] and "INSERT INTO measurement" not in sql


def test_m4_icd10_without_the_dot_gets_it_back():
    sql, _ = _leer(_cond(code={"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "Z992"}]}))
    assert "'Z99.2'" in sql


def test_l1_a_declined_participant_is_not_the_patient_of_the_visit():
    cita = {"resourceType": "Appointment", "id": "a1", "status": "booked", "start": "2026-11-14T10:00:00+01:00",
            "participant": [{"actor": {"reference": "Patient/p1"}, "status": "declined"}]}
    _, inf = _leer(cita)
    assert not inf["extracto_completo"] and "visit" not in str(inf["cargado"])


def test_inactive_patients_resources_are_ignored_not_misattributed():
    b = _bundle(_obs(subject={"reference": "Patient/p0"}))
    b["entry"].append({"resource": {"resourceType": "Patient", "id": "p0", "birthDate": "1950", "active": False}})
    sql, inf = bundle_a_extracto(b)
    assert inf["extracto_completo"] and "INSERT INTO measurement" not in sql


@pytest.mark.parametrize("parche", [
    {"status": ["final"]}, {"code": {"coding": [{"system": ["x"], "code": "9318-7"}]}}, {"code": {"coding": 5}},
    {"effectivePeriod": [1]}, {"valueQuantity": {"value": 10 ** 400, "unit": "mg/g"}}, {"subject": "Patient/p1"},
    {"subject": {"reference": 7}}, {"valueQuantity": [12]}, {"component": 5},
])
def test_h8_malformed_shapes_are_refused_cleanly(parche):
    obs = _obs()
    obs.update(parche)
    with pytest.raises(BundleInvalido):
        bundle_a_extracto(_bundle(obs))


@pytest.mark.parametrize("tipo", ["Descartar", "Medicacion", "Visita", "observation", "Resolver"])
def test_h9_resource_type_cannot_reach_a_private_method(tipo):
    _, inf = _leer({"resourceType": tipo, "id": "x", "subject": {"reference": "Patient/p1"}})
    assert inf["ignorado_sin_efecto"] == {tipo: 1}


def test_fuzz_only_success_or_a_clean_refusal():
    """Random shape damage to a real synthetic bundle: the reader either succeeds or raises BundleInvalido."""
    import random
    base = json.loads((ROOT / "data/synthetic/fhir/demo_bundle.json").read_text(encoding="utf-8"))
    raros = [None, 5, "x", [], {}, [1], {"a": 1}, True, 1e308, -1, "2026-13-40", "Patient/zz", float("nan")]
    rng = random.Random(20261116)
    for _ in range(400):
        b = json.loads(json.dumps(base))
        r = rng.choice(b["entry"])["resource"]
        clave = rng.choice(sorted(r))
        r[clave] = rng.choice(raros)
        try:
            sql, _ = bundle_a_extracto(b, sistemas_cie=CIE, sistema_sip=SISTEMA_SIP)
            ejecutar.generar(ejecutar.construir(sql))
        except BundleInvalido:
            pass


# -- re-review of PR 16 ----------------------------------------------------------------------------------------
def _dos_pacientes(obs, url1=None, url2=None):
    b = _bundle(obs)
    b["entry"][0]["resource"]["id"] = "1"
    b["entry"].append({"resource": {"resourceType": "Patient", "id": "2", "birthDate": "1950"}})
    if url1:
        b["entry"][0]["fullUrl"] = url1
    if url2:
        b["entry"][-1]["fullUrl"] = url2
    return b


@pytest.mark.parametrize("ref,url1", [
    ("https://other.example/fhir/Patient/2", None),
    ("https://b/fhir/Patient/1", "https://a/fhir/Patient/1"),
    ("http://x/Group/Patient/2", None),
])
def test_an_absolute_reference_must_be_this_bundles_patient(ref, url1):
    sql, inf = bundle_a_extracto(_dos_pacientes(_obs(subject={"reference": ref}), url1))
    assert not inf["extracto_completo"] and "INSERT INTO measurement" not in sql


def test_the_exact_fullurl_with_history_still_resolves():
    b = _dos_pacientes(_obs(subject={"reference": "https://a/fhir/Patient/1/_history/2"}), "https://a/fhir/Patient/1")
    sql, inf = bundle_a_extracto(b)
    assert inf["extracto_completo"] and _row_people(sql) == {inf["pacientes"]["1"]}


def test_a_fullurl_that_contradicts_the_id_is_refused():
    with pytest.raises(BundleInvalido, match="no coincide"):
        bundle_a_extracto(_dos_pacientes(_obs(subject={"reference": "Patient/2"}), "Patient/2", "urn:uuid:b"))


def test_a_rule_component_next_to_a_top_level_code_is_flagged():
    obs = _obs(component=[{"code": {"coding": [{"system": "http://loinc.org", "code": "62238-1"}]},
                           "valueQuantity": {"value": 40, "unit": "mL/min/1.73m2"}}])
    sql, inf = _leer(obs)
    assert not inf["extracto_completo"] and "'9318-7'" in sql and "'62238-1'" not in sql


@pytest.mark.parametrize("valor", ["true", 1, None])
def test_do_not_perform_must_be_a_boolean(valor):
    sr = {"resourceType": "ServiceRequest", "id": "s1", "status": "active", "intent": "order", "doNotPerform": valor,
          "subject": {"reference": "Patient/p1"}, "authoredOn": "2026-11-01",
          "code": {"coding": [{"system": "http://loinc.org", "code": "9318-7"}]}}
    with pytest.raises(BundleInvalido, match="doNotPerform"):
        _leer(sr)


@pytest.mark.parametrize("total", ["50", 50.0, True])
def test_bundle_total_must_be_an_integer(total):
    b = _bundle(_obs())
    b["total"] = total
    with pytest.raises(BundleInvalido, match="total"):
        bundle_a_extracto(b)


def test_a_note_part_that_is_not_plain_text_is_flagged():
    doc = {"resourceType": "DocumentReference", "id": "d1", "status": "current", "subject": {"reference": "Patient/p1"},
           "date": "2026-10-01T00:00:00Z",
           "content": [{"attachment": {"contentType": "text/plain", "data": base64.b64encode(b"Control DM2.").decode()}},
                       {"attachment": {"contentType": "application/pdf", "data": "JVBERi0="}}]}
    sql, inf = _leer(doc)
    assert not inf["extracto_completo"] and "Control DM2." in sql
