"""Vuelta 13 (signed by Ahmed, 16 Nov 2026; docs/FIRMA_VUELTA_13.md): one test per reproduced finding, plus a
near-miss that must keep the old behaviour. Reference date 2026-11-14. Software verification, not clinical validation.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from ejecutar import construir, generar  # noqa: E402
from test_notas import lector_fijo, nota_sql, por_frase  # noqa: E402
from test_reglas import META, cac, correr, fge, fuera, medida, persona, reglas  # noqa: E402


def codigo(pid, cod, fecha, cid):
    return (f"INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, "
            f"condition_start_date, condition_type_concept_id, condition_source_value) "
            f"VALUES ({cid}, {pid}, 0, '{fecha}', 0, '{cod}');\n")


def pedido(res, pid):
    return next(p for p in res["pedidos"] if p["person_id"] == pid)


# --- R1: persistence from two lab results -------------------------------------------------------------------------

def test_dos_cac_alterados_de_laboratorio_son_persistentes():
    res = correr(persona(1) + cac(1, "2024-01-10", 120) + cac(1, "2024-06-10", 150))
    assert reglas(res, 1) == {"S1d"}
    p = pedido(res, 1)
    assert p["pedido"] == "Albuminuria persistente en dos analíticas: valorar código de ERC (N18)"
    assert "120 mg/g (2024-01-10) → 150 mg/g (2024-06-10)" in p["motivo"]


def test_s1d_aunque_el_ultimo_sea_reciente():
    # S1b needs >6 months without a repeat; persistence does not.
    res = correr(persona(1) + cac(1, "2026-02-01", 60) + cac(1, "2026-10-01", 80))
    assert reglas(res, 1) == {"S1d"}


def test_un_cac_normal_entre_medias_rompe_la_persistencia():
    res = correr(persona(1) + cac(1, "2024-01-10", 120) + cac(1, "2024-03-10", 12) + cac(1, "2024-06-10", 150))
    assert reglas(res, 1) == {"S1b"}


def test_menos_de_3_meses_entre_los_dos_sigue_siendo_s1b():
    res = correr(persona(1) + cac(1, "2024-04-10", 120) + cac(1, "2024-06-10", 150))
    assert reglas(res, 1) == {"S1b"}


def test_s1d_en_mg_mmol():
    res = correr(persona(1) + cac(1, "2024-01-10", 4, "mg/mmol", "14958-3") + cac(1, "2024-06-10", 35))
    assert reglas(res, 1) == {"S1d"}


# --- R2: exclusions ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("cod,motivo", [("Z99.2", "diálisis"), ("N18.6", "diálisis"), ("Z49.01", "diálisis"),
                                        ("Z94.0", "trasplante renal"), ("Z51.5", "cuidados paliativos")])
def test_exclusiones_van_fuera_con_motivo(cod, motivo):
    res = correr(persona(1, codigos=("E11.9", cod)))
    assert reglas(res, 1) == set()
    assert fuera(res, 1) == [f"Excluido: {motivo}"]


def test_embarazo_reciente_excluye():
    res = correr(persona(1, codigos=("E11.9",)) + codigo(1, "O24.4", "2026-06-01", 9001) + cac(1, "2025-10-01", 45))
    assert reglas(res, 1) == set() and fuera(res, 1) == ["Excluido: embarazo o puerperio reciente"]


def test_embarazo_antiguo_no_excluye():
    res = correr(persona(1, codigos=("E11.9",)) + codigo(1, "O24.4", "2019-06-01", 9001) + cac(1, "2025-10-01", 45))
    assert reglas(res, 1) == {"S1b"}


def test_sin_edad_limite():
    res = correr(persona(1, nacimiento=1934, codigos=("I10",)))
    assert reglas(res, 1) == {"S1a"}


# --- R3: one equation per trend ------------------------------------------------------------------------------------

def test_cambio_de_ecuacion_no_inventa_un_descenso():
    # Stable creatinine; the lab switched from CKD-EPI 2009 to MDRD, which reads lower.
    sql = (persona(1) + cac(1, "2026-08-01", 5) + fge(1, "2024-03-01", 82) + fge(1, "2025-03-01", 81)
           + medida(1, "2026-03-01", 66, "mL/min/1.73m2", "33914-3") + medida(1, "2026-10-01", 64, "mL/min/1.73m2", "33914-3"))
    res = correr(sql)
    assert "S3" not in reglas(res, 1) and "S3c" not in reglas(res, 1)
    assert fuera(res, 1) == ["Información insuficiente: FGe de distintas ecuaciones (MDRD, CKD-EPI); no se calcula la tendencia"]


def test_misma_ecuacion_sigue_detectando_el_descenso():
    sql = (persona(1) + cac(1, "2026-08-01", 5) + fge(1, "2024-03-01", 82) + fge(1, "2025-03-01", 72)
           + fge(1, "2026-10-01", 60) + medida(1, "2023-01-01", 90, "mL/min/1.73m2", "33914-3"))
    assert reglas(correr(sql), 1) == {"S3"}


def test_mismo_dia_dos_ecuaciones_no_se_promedian():
    sql = (persona(1, codigos=("I10",)) + cac(1, "2026-08-01", 5)
           + medida(1, "2026-10-01", 58, "mL/min/1.73m2", "98979-8") + medida(1, "2026-10-01", 64, "mL/min/1.73m2", "62238-1"))
    res = correr(sql)
    # The 2021 value (58) is the last one: below 60, so the person is in the population; no average of 61.
    assert res["pacientes_revisados"] == 1


# --- R4: hypertensive and diabetic kidney codes count as CKD ------------------------------------------------------

@pytest.mark.parametrize("cod", ["I12.9", "I13.0", "E11.21", "E11.22"])
def test_codigo_renal_no_pide_codificar(cod):
    res = correr(persona(1, codigos=("I10", cod)) + cac(1, "2025-10-01", 90))
    assert "S1b" not in reglas(res, 1) and "S1d" not in reglas(res, 1)


def test_i12_sigue_en_la_poblacion_de_cribado():
    assert reglas(correr(persona(1, codigos=("I12.9",))), 1) == {"S1a"}


# --- R5: a note never removes an eGFR order ------------------------------------------------------------------------

def test_nota_con_fge_bajo_no_retira_s3c():
    texto = "Se aporta FGe 22 ml/min el 10/11/2026."
    sql = (persona(1) + cac(1, "2026-08-01", 5) + fge(1, "2025-06-01", 60) + fge(1, "2026-10-01", 20)
           + nota_sql(1, 1, "2026-11-12", texto))
    res = generar(construir(META.format(completo=1) + sql,
                            lector=lector_fijo({texto: por_frase("ya_realizada", 1, "FGe", "2026-11-10")})))
    assert reglas(res, 1) == {"S3c"} and fuera(res, 1) == []
    assert any("FGe" in a for a in pedido(res, 1)["anotaciones"])


def test_nota_con_cac_normal_sigue_retirando_s1a():
    texto = "Trae informe de la mutua: CAC 12 mg/g el 03/10/2026."
    sql = persona(1, codigos=("I10",)) + nota_sql(1, 1, "2026-11-12", texto)
    res = generar(construir(META.format(completo=1) + sql,
                            lector=lector_fijo({texto: por_frase("ya_realizada", 1, "CAC", "2026-10-03")})))
    assert reglas(res, 1) == set() and fuera(res, 1)[0].startswith("Ya cubierto")


# --- R6: impossible values -----------------------------------------------------------------------------------------

def test_cac_negativo_es_informacion_insuficiente():
    res = correr(persona(1, codigos=("I10",)) + cac(1, "2026-09-01", -5))
    assert any("valor imposible" in m for m in fuera(res, 1))


@pytest.mark.parametrize("valor", [0, 5000])
def test_fge_imposible_es_informacion_insuficiente(valor):
    sql = (persona(1, codigos=("I10",)) + cac(1, "2026-08-01", 5) + fge(1, "2025-01-01", 80) + fge(1, "2025-12-01", 79)
           + fge(1, "2026-10-01", valor))
    res = correr(sql)
    assert "S3" not in reglas(res, 1) and "S3c" not in reglas(res, 1)
    assert fuera(res, 1) == [f"Información insuficiente: FGe con valor imposible ({valor})"]


def test_fge_cero_no_mete_en_la_poblacion():
    res = correr(persona(1, codigos=()) + fge(1, "2026-10-01", 0))
    assert res["pacientes_revisados"] == 0


# --- R7: the repeat order names the sample -------------------------------------------------------------------------

def test_s1b_pide_primera_orina_de_la_manana():
    p = pedido(correr(persona(1) + cac(1, "2025-10-01", 45)), 1)
    assert p["pedido"] == "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana"
    assert "chorro medio" in p["nota"] and "menstruación" in p["nota"] and "1.3.1.2" in p["nota"]


# --- D: type 1 diabetes, 5 years after the first code --------------------------------------------------------------

def test_dm1_de_mas_de_5_anos_entra_en_el_cribado():
    res = correr(persona(1, codigos=()) + codigo(1, "E10.9", "2020-01-01", 9001))
    assert reglas(res, 1) == {"S1a"}


def test_dm1_de_menos_de_5_anos_no():
    res = correr(persona(1, codigos=()) + codigo(1, "E10.9", "2023-01-01", 9001))
    assert reglas(res, 1) == set()


# --- N1: the follow-up word must refer to Nephrology ----------------------------------------------------------------

from notas.verificar import verificar  # noqa: E402


def nef(texto):
    return verificar(texto, "2026-06-01", {"etiqueta": "nefrologia", "prueba": None, "fecha_en_nota": None, "frase": 1},
                     "2026-06-01")[0]["verificada"]


def test_ingreso_con_reposicion_controlada_se_rechaza():
    assert nef("Se ingresó en Nefrología con el diagnóstico de IRA prerrenal, hipernatremia e infección urinaria, se "
               "inició tratamiento antibiótico y reposición hidroelectrolítica controlada con buena respuesta, siendo "
               "la creatinina al alta de 0,86 mg/dl.") == 0


@pytest.mark.parametrize("texto", [
    "Es seguida por el servicio de nefrología por el empeoramiento de la función renal.",
    "Se mantuvo en seguimiento en policlínico de infectología y nefrología, con evolución favorable.",
    "Actualmente se mantiene en control en el policlínico de nefrología de nuestro hospital.",
    "A los 45 años es derivada a Consultas de Nefrología para seguimiento.",
    "En la actualidad el paciente está bajo control y seguimiento por el Servicio de Nefrología presentando creatinina 1,2.",
    "Paciente de 17 años, en control por nefrología infantil, afecta de esclerosis tuberosa.",
])
def test_seguimiento_cerca_de_nefrologia_se_acepta(texto):
    assert nef(texto) == 1


def test_seguimiento_en_otra_clausula_se_rechaza():
    # Signed choice B: an inpatient sentence whose "controles" sits in another clause is a miss in the safe direction.
    assert nef("El caso es valorado conjuntamente con el servicio de nefrología, consensuando una actitud expectante; "
               "la paciente continúa hospitalizada para proseguir sus controles.") == 0


# --- Vuelta 14 (signed 16 Nov 2026): an admission word in the same clause cancels the follow-up word -------------

@pytest.mark.parametrize("texto", [
    "Ingresó en Nefrología para control de la tensión arterial.",
    "Se ingresa en el servicio de Nefrología por IRA con control analítico diario.",
    "Hospitalizado en Nefrología para control de la volemia.",
])
def test_ingreso_con_palabra_de_control_se_rechaza(texto):
    assert nef(texto) == 0


@pytest.mark.parametrize("texto", [
    "Tras el alta, se mantiene en seguimiento en consultas de Nefrología.",
    "Ingresó por neumonía en 2019; actualmente en control por Nefrología cada seis meses.",
    "Fue derivado a Nefrología para seguimiento.",   # round 11, signed choice 1: a referral for follow-up counts
])
def test_seguimiento_sin_ingreso_en_la_clausula_se_acepta(texto):
    assert nef(texto) == 1
