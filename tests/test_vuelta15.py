"""Round 15 reading rules, V2-V7 signed by Ahmed on 16 Nov 2026 ("B: sign V2-V7, hold V1"); V1 held.
docs/FIRMA_VUELTA_15.md; protocol amendments 10-15.

Each row is a probe from the error log (E-14..E-19, E-42..E-46), the code review or the real held-out 2 text.
"""
import pytest

from notas.verificar import frases, no_es_cac, valor_en, verificar

NOTA, HOY = "2026-11-01", "2026-11-16"

CAC = [
    # V1 HELD (failed three blind sets): another test's number in the sentence still blocks the CAC value (E-17)
    ("creatinina sérica (Cr) 0.92mg/dl (FG por CKD-EPI 93ml/min, cociente albumina/creatinina 57mg/g, sedimento orina normal)", (None, None)),
    ("Hb 12,1 g/dl, potasio 4,5 mEq/l, CAC 20 mg/g, TA 130/80 mmHg, HbA1c 7,2 %, peso 70 kg", (None, None)),
    ("CAC 36 mg/g y CPC 0.130 g/g, orina de 24 h", (None, None)),
    ("creatinina 0,9 mg/dl, CAC 20 mg/g", (None, None)),
    ("CAC 25 mg/g y ACR 450 mg/L", (None, None)),                 # E-50 (only V1 read 25)
    ("CAC 2 mg/mmol o menos, urea 29 mg/dl", (None, None)),        # E-47 (only V1 read 2)
    # a lone result is still read
    ("CAC 20 mg/g", (20.0, "mg/g")),
    ("Índice albumina/creatinina 57 mg/g", (57.0, "mg/g")),
    # a number without a unit still blocks; two CACs still ambiguous
    ("creatinina 0,9 mg/dl, cociente albúmina/creatinina de 3,5", (None, None)),
    ("CAC 40 mg/g, 2", (None, None)),
    ("CAC 25 mg/g y en la repetición 80 mg/g", (None, None)),
    # E-46: a second CAC in a wrong unit keeps the reading ambiguous
    ("CAC 25 mg/g y CAC 450 mg/L", (None, None)),
    ("CAC 450 mg/g, CAC 25 mg/dl", (None, None)),
    ("microalbuminuria 25 mg/g, microalbuminuria 450 mg/l", (None, None)),
    # E-42, E-45: bounds in words are not values
    ("CAC menos de 30 mg/g, K 4 mEq/l", (None, None)),
    ("CAC más de 300 mg/g, K 4 mEq/l", (None, None)),
    ("Microalbuminuria por encima de 300 mg/g, K 5,2 mEq/l", (None, None)),
    ("CAC por debajo de 30 mg/g", (None, None)),
    ("CAC hasta 30 mg/g", (None, None)),
    ("albuminuria ‹3 mg/g", (None, None)),
    ("CAC < 30 mg/g, Hb 12 g/dl", (None, None)),
]


@pytest.mark.parametrize("frase,esperado", CAC)
def test_cac_value(frase, esperado):
    assert valor_en(frase, "CAC") == esperado


FGE = [
    ("FG > 60, creatinina 0,5 mg/dl", (None, None)),            # E-16, V4
    ("FGe mayor de 60 ml/min", (None, None)),
    ("FGe CKD-EPI 2021 de 57, Hb 12 g/dl", (57.0, None)),       # E-44, V5
    ("FG (CKD-EPI 2009) 44 ml/min/1,73 m2", (44.0, None)),
    ("FGe CKD-EPI 2009-2021 57", (57.0, None)),
    ("FG MDRD-4 38", (38.0, None)),
    ("FG por CKD-EPI 93 ml/min", (93.0, None)),                 # a value after the name is still read
    ("FG MDRD 45", (45.0, None)),
    ("FGe Cockcroft-Gault 90 kg 57", (None, None)),             # code review: the weight is not the eGFR
    ("FG Cockcroft-Gault (peso 90 kg) 57 ml/min", (None, None)),
    ("FG 45 ml/min, peso 70 kg", (45.0, None)),
]


@pytest.mark.parametrize("frase,esperado", FGE)
def test_fge_value(frase, esperado):
    assert valor_en(frase, "FGe") == esperado


@pytest.mark.parametrize("frase,esperado", [
    ("uroanálisis con albuminuria ++++", True),                 # E-14, V3
    ("albuminuria, 4.5 g/24 h", True),                          # E-15
    ("microalbuminuria 25 mg/l", True),
    ("albuminuria ++, glucosa 110 mg/dl", True),
    ("sin microalbuminuria, colesterol LDL 136 mg/dl", False),  # amendment 12: the gap may not cross a comma
    ("CAC 20 mg/g y microalbuminuria 25 mg/l", False),          # names the ACR / has an mg/g value
    ("albuminuria 29,8 mg/dl, creatinina 107 mg/dl, cociente albúmina/creatinina 278 mg/g", False),
])
def test_no_es_cac(frase, esperado):
    assert no_es_cac(frase) is esperado


def _cac(nota, k=1):
    salida = {"etiqueta": "ya_realizada", "prueba": "CAC", "fecha_en_nota": None, "frase": k}
    return [f for f in verificar(nota, NOTA, salida, HOY) if f["verificada"] == 1 and f.get("prueba") == "CAC"]


def test_v2_names_the_acr():
    assert _cac("Índice albumina/creatinina 57 mg/g.")[0]["valor"] == 57.0
    assert _cac("Cociente microalbúmina/creatinina de 76 mg/g.")[0]["valor"] == 76.0


def test_v3_rejects_a_dipstick():
    assert _cac("Uroanálisis con albuminuria ++++.") == []


def test_e43_split_sentence_is_read_whole():
    nota = "CAC 18 mg/g (03/05/2023); CAC 52 mg/g (14/09/2023); LDL 99 mg/dl."
    assert len(frases(nota)) == 3
    for k in (1, 2):
        (fila,) = _cac(nota, k)
        assert fila["valor"] is None and fila["fecha_cita"] is None   # ambiguous: removes and adds nothing


def test_a_clean_single_result_with_a_date_still_works():
    (fila,) = _cac("CAC 12 mg/g el 03/05/2026.")
    assert (fila["valor"], fila["fecha_cita"]) == (12.0, "2026-05-03")


def test_signed_rescores_match_readme_and_claims():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    res = [json.loads((root / f"eval/results/ciego_v15_set{n}_signed.json").read_text(encoding="utf-8")) for n in (1, 2, 3)]
    before = [r["versions"]["before"]["unsafe"] for r in res]
    after = [r["versions"]["after"]["unsafe"] for r in res]
    assert (before, after) == ([16, 21, 28], [0, 0, 4])
    limitations = (root / "docs/LIMITATIONS.md").read_text(encoding="utf-8")
    assert "fell from 16, 21 and 28 to 0, 0 and 4" in limitations
    assert "16 / 21 / 28 (round 14) → 0 / 0 / 4" in (root / "docs/CLAIMS.md").read_text(encoding="utf-8")
