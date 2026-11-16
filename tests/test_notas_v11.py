"""Vuelta 11 of the note checks (signed by Ahmed, 16 Nov 2026), from the real-text test (CodiEsp).

Each real error has a test, built from the real sentence. Each one also has a near-miss that must still pass, so the
fix doesn't overreach. No model is called. This is software verification, not clinical validation.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from notas.verificar import verificar  # noqa: E402

HOY = NOTA = "2026-06-01"


def una(texto, etiqueta, prueba=None):
    filas = verificar(texto, NOTA, {"etiqueta": etiqueta, "prueba": prueba, "fecha_en_nota": None, "frase": 1}, HOY)
    return filas[0]


# --- "followed in Nephrology" must say follow-up --------------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "El paciente es valorado por el Servicio de Nefrología, instaurándose tratamiento con furosemida 40 mg diarios.",
    "Tras valoración por el Servicio de Nefrología, se inició tratamiento con diálisis.",
    "La envían a Nefrología por detectar proteinuria de +++.",
    "Nefrología confirma diagnóstico de insuficiencia renal aguda secundaria a aciclovir.",
    "En el año 2009 es derivado a consulta de nefrología por enfermedad renal crónica estadio 2.",
    "Roberto León Instituto de Nefrología Sa Buenos Aires.",
    "Se solicita interconsulta a Nefrología.",
])
def test_nefrologia_sin_seguimiento_se_rechaza(texto):
    h = una(texto, "nefrologia")
    assert h["verificada"] == 0 and "seguimiento" in h["motivo_rechazo"]


@pytest.mark.parametrize("texto", [
    "Es seguida por el servicio de nefrología por el empeoramiento de la función renal.",
    "Se mantuvo en seguimiento en policlínico de infectología y nefrología, con evolución favorable.",
    "Se controló en consultas de Nefrología Pediátrica.",
    "Lo controlan en consultas externas de Nefrología del H. General.",
    "Actualmente se mantiene en control en el policlínico de nefrología de nuestro hospital.",
    "A los 45 años es derivada a Consultas de Nefrología para seguimiento.",
    "Acude a consultas de Nefrología cada seis meses.",
])
def test_nefrologia_con_seguimiento_se_acepta(texto):
    assert una(texto, "nefrologia")["verificada"] == 1


def test_nefrologia_negada_sigue_rechazada():
    assert una("No está seguido en Nefrología.", "nefrologia")["verificada"] == 0


# --- a refusal must be of the test ------------------------------------------------------------------------------

def test_rechazo_de_otro_tratamiento_se_rechaza():
    h = una("Debido al rechazo del paciente a otro tratamiento inmunosupresor, se inició GCAP.", "rechazo")
    assert h["verificada"] == 0 and "otra cosa" in h["motivo_rechazo"]


@pytest.mark.parametrize("texto", [
    "No quiere hacerse la analítica de este año.",
    "Rechaza la analítica de orina.",
    "No quiere hacerse la muestra de orina ni otro tratamiento.",
])
def test_rechazo_de_la_prueba_se_sigue_aceptando(texto):
    assert una(texto, "rechazo")["verificada"] == 1


# --- values the code now reads ------------------------------------------------------------------------------------

def test_cac_con_otra_medida_de_orina_en_la_frase():
    h = una("El estudio de orina mostró un índice microalbuminuria/creatininuria de 261,9 mg/g y "
            "proteinuria/creatininuria 1,1 sin síndrome nefrótico.", "ya_realizada", "CAC")
    assert h["verificada"] == 1 and (h["valor"], h["unidad"]) == (261.9, "mg/g")


def test_proteinuria_en_mg_g_no_se_lee_como_cac():
    h = una("Microalbuminuria realizada; proteinuria/creatininuria 300 mg/g.", "ya_realizada", "CAC")
    assert h["valor"] is None


def test_microgramos_por_mg_es_mg_g():
    h = una("Cociente albúmina/creatinina: 0,6µg/mgr.", "ya_realizada", "CAC")
    assert (h["valor"], h["unidad"]) == (0.6, "mg/g")


def test_dos_cac_distintos_siguen_siendo_ambiguos():
    h = una("CAC 40 mg/g y después CAC 25 µg/mg.", "ya_realizada", "CAC")
    assert h["valor"] is None


def test_fge_lejos_del_nombre_con_unidad():
    h = una("Presenta creatinina (Cr) 2,3mg/dl, filtrado glomerular estimado (FGe) MDRD (Modification of Diet in "
            "Renal Disease) 34ml/min/1,73m2, proteinuria de 10mg/dl.", "ya_realizada", "FGe")
    assert h["verificada"] == 1 and h["valor"] == 34.0


def test_fge_lejos_del_nombre_sin_unidad_no_se_lee():
    h = una("FGe estimado por la fórmula del laboratorio de referencia: 34.", "ya_realizada", "FGe")
    assert h["valor"] is None
