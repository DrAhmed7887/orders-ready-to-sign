"""Synthetic extract (data/schema.sql INSERTs) → FHIR R4 Bundle. Only to build test bundles from the synthetic sets.

    python3 fhir/extracto_a_fhir.py data/synthetic/demo_seed.sql -o data/synthetic/fhir/demo_bundle.json

A real record system would export FHIR itself; this script exists so the FHIR reader can be checked end to end on
the same synthetic patients the rules were tested on (round trip: extract → FHIR → extract → same orders).
Local URIs for the synthetic CIE-10-ES codes and SIP numbers: SISTEMA_CIE and SISTEMA_SIP.
"""
from __future__ import annotations

import argparse
import base64
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

RAIZ = Path(__file__).resolve().parents[1]
SISTEMA_CIE = "urn:sintetico:cie-10-es"
SISTEMA_SIP = "urn:sintetico:sip"
LOINC_PEDIDO = {"CAC": "9318-7", "FGe": "62238-1"}
GENERO = {8507: "male", 8532: "female"}


def _cargar(extracto_sql: str) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript((RAIZ / "data" / "schema.sql").read_text(encoding="utf-8"))
    con.executescript(extracto_sql)
    return con


def extracto_a_bundle(extracto_sql: str) -> Dict[str, Any]:
    con = _cargar(extracto_sql)
    meta = con.execute("SELECT * FROM extract_meta").fetchone()
    entradas: List[Dict[str, Any]] = []

    def add(r: Dict[str, Any]) -> None:
        entradas.append({"fullUrl": f"urn:uuid:{r['id']}", "resource": r})

    def ref(pid: int) -> Dict[str, str]:
        return {"reference": f"urn:uuid:pac-{pid}"}

    sip = {r["person_id"]: r["value_as_string"] for r in con.execute(
        "SELECT person_id, value_as_string FROM observation WHERE observation_source_value = 'SIP_SINTETICO'")}
    for p in con.execute("SELECT * FROM person ORDER BY person_id"):
        r: Dict[str, Any] = {"resourceType": "Patient", "id": f"pac-{p['person_id']}", "birthDate": str(p["year_of_birth"])}
        if p["gender_concept_id"] in GENERO:
            r["gender"] = GENERO[p["gender_concept_id"]]
        if p["person_source_value"]:
            r["name"] = [{"text": p["person_source_value"]}]
        if p["person_id"] in sip:
            r["identifier"] = [{"system": SISTEMA_SIP, "value": sip[p["person_id"]]}]
        add(r)
    for c in con.execute("SELECT * FROM condition_occurrence ORDER BY condition_occurrence_id"):
        add({"resourceType": "Condition", "id": f"cond-{c['condition_occurrence_id']}", "subject": ref(c["person_id"]),
             "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                                "code": "confirmed"}]},
             "code": {"coding": [{"system": SISTEMA_CIE, "code": c["condition_source_value"]}]},
             "onsetDateTime": c["condition_start_date"]})
    for m in con.execute("SELECT * FROM measurement ORDER BY measurement_id"):
        r = {"resourceType": "Observation", "id": f"obs-{m['measurement_id']}", "status": "final",
             "subject": ref(m["person_id"]), "effectiveDateTime": m["measurement_date"],
             "code": {"coding": [{"system": "http://loinc.org", "code": m["measurement_source_value"]}]}}
        if m["value_as_number"] is None:
            r["dataAbsentReason"] = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                                                 "code": "unknown"}]}
        else:
            r["valueQuantity"] = {"value": m["value_as_number"], **({"unit": m["unit_source_value"]}
                                                                    if m["unit_source_value"] is not None else {})}
        add(r)
    for d in con.execute("SELECT * FROM drug_exposure ORDER BY drug_exposure_id"):
        add({"resourceType": "MedicationStatement", "id": f"med-{d['drug_exposure_id']}", "status": "completed",
             "subject": ref(d["person_id"]),
             "medicationCodeableConcept": {"coding": [{"system": "http://www.whocc.no/atc", "code": d["drug_source_value"]}]},
             "effectivePeriod": {"start": d["drug_exposure_start_date"], "end": d["drug_exposure_end_date"]}})
    for v in con.execute("SELECT * FROM visit_occurrence ORDER BY visit_occurrence_id"):
        if v["visit_start_datetime"]:
            add({"resourceType": "Appointment", "id": f"cita-{v['visit_occurrence_id']}", "status": "booked",
                 "start": v["visit_start_datetime"].replace(" ", "T")[:16] + ":00+01:00",
                 "participant": [{"actor": ref(v["person_id"]), "status": "accepted"}]})
        else:
            add({"resourceType": "Encounter", "id": f"enc-{v['visit_occurrence_id']}", "status": "planned",
                 "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
                 "subject": ref(v["person_id"]), "period": {"start": v["visit_start_date"]}})
    for n in con.execute("SELECT * FROM note ORDER BY note_id"):
        r = {"resourceType": "DocumentReference", "id": f"nota-{n['note_id']}", "status": "current",
             "subject": ref(n["person_id"]), "date": n["note_date"] + "T00:00:00+01:00",
             "content": [{"attachment": {"contentType": "text/plain; charset=utf-8",
                                         "data": base64.b64encode(n["note_text"].encode("utf-8")).decode("ascii")}}]}
        if n["note_title"]:
            r["description"] = n["note_title"]
        add(r)
    for s in con.execute("SELECT * FROM pedido_pendiente ORDER BY pedido_id"):
        add({"resourceType": "ServiceRequest", "id": f"ped-{s['pedido_id']}", "status": "active", "intent": "order",
             "subject": ref(s["person_id"]), "authoredOn": s["fecha_pedido"],
             "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_PEDIDO[s["prueba"]]}]}})
    return {"resourceType": "Bundle", "type": "collection", "timestamp": meta["fecha_referencia"] + "T00:00:00+01:00",
            "meta": {"tag": [{"system": "urn:sintetico", "code": "synthetic", "display": "Solo datos sintéticos"}]},
            "entry": entradas}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extracto", type=Path)
    ap.add_argument("-o", "--salida", type=Path, required=True)
    args = ap.parse_args(argv)
    b = extracto_a_bundle(args.extracto.read_text(encoding="utf-8"))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(b['entry'])} recursos → {args.salida}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
