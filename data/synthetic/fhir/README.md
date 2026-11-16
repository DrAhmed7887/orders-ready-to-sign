# Synthetic FHIR R4 bundles

Generated from the synthetic extracts by `python3 fhir/extracto_a_fhir.py <extract.sql> -o <bundle.json>`; the test
`tests/test_fhir.py::test_committed_bundles_are_current` checks they are current. **Synthetic only, no real patient.**

| File | From | Resources |
|---|---|---|
| `demo_bundle.json` | `data/synthetic/demo_seed.sql` | Patient, Condition, Observation, Appointment, ServiceRequest |
| `aguja_bundle.json` | `data/synthetic/aguja/extracto.sql` (Amparo among 250) | the above plus DocumentReference (notes), MedicationStatement, Encounter |

Local code systems (the FHIR R4 spec lists no URI for CIE-10-ES): `urn:sintetico:cie-10-es` for diagnoses and
`urn:sintetico:sip` for the synthetic SIP number. Pass them to the reader with `--sistema-cie` and `--sistema-sip`.
Run the engine on a bundle: `python3 ejecutar.py data/synthetic/fhir/aguja_bundle.json --sistema-cie urn:sintetico:cie-10-es --sistema-sip urn:sintetico:sip`.
