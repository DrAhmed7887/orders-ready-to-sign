"""Unit tests for the NHANES evaluation (no network, no pandas)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval" / "nhanes"))

from core import Participant, egfr_ckd_epi_2021, extract_sql, flags_from_engine, in_population, survey_proportion  # noqa: E402
from ejecutar import construir, generar  # noqa: E402


@pytest.mark.parametrize("scr,age,female,expected", [
    (0.7, 50, True, 105.3),    # Scr/K = 1: 142 * 0.9938^50 * 1.012
    (1.8, 60, False, 42.6),    # Scr/K = 2: 142 * 2^-1.2 * 0.9938^60
    (0.45, 40, False, 136.5),  # Scr/K = 0.5: 142 * 0.5^-0.302 * 0.9938^40 = 142 * 1.2328 * 0.7798
])
def test_egfr_hand_computed(scr, age, female, expected):
    assert egfr_ckd_epi_2021(scr, age, female) == pytest.approx(expected, abs=0.1)


def test_egfr_rejects_bad_input():
    with pytest.raises(ValueError):
        egfr_ckd_epi_2021(0, 50, True)


def test_survey_proportion_simple():
    # 2 strata x 2 PSUs, equal weights: p = 2/8
    y = [1, 0, 0, 0, 1, 0, 0, 0]
    est = survey_proportion(y, [1] * 8, [1.0] * 8, [1, 1, 1, 1, 2, 2, 2, 2], [1, 1, 2, 2, 1, 1, 2, 2])
    assert est.p == pytest.approx(0.25)
    assert est.lo < 0.25 < est.hi
    assert (est.n, est.events) == (8, 2)


def test_survey_domain_keeps_weights_out_of_domain():
    est = survey_proportion([1, 0, 1, 1], [1, 1, 0, 0], [2.0, 2.0, 5.0, 5.0], [1, 1, 1, 1], [1, 2, 1, 2])
    assert est.p == pytest.approx(0.5)
    assert est.n == 2


def test_population_filter():
    assert in_population(45, False, True, False, 0.9, 12.0, 1000.0)
    assert not in_population(17, False, True, False, 0.9, 12.0, 1000.0)   # child
    assert not in_population(45, True, True, False, 0.9, 12.0, 1000.0)    # pregnant
    assert not in_population(45, False, False, False, 0.9, 12.0, 1000.0)  # neither condition
    assert not in_population(45, False, True, True, None, 12.0, 1000.0)   # no creatinine


def _p(seqn, scr, acr, female=False, age=60):
    return Participant(seqn, age, female, True, True, scr, acr, 1.0, 1, 1)


def test_one_visit_mapping_runs_the_unmodified_engine():
    people = [
        _p(1, 0.9, 85.0),   # eGFR ~ 92, ACR 85: hidden albuminuria -> S1b, baseline misses
        _p(2, 1.8, 10.0),   # eGFR ~ 43, ACR normal -> baseline only
        _p(3, 0.9, 12.0),   # nothing
        _p(4, 0.9, 30.0),   # exactly 30 mg/g -> S1b (>= 30)
        _p(5, 0.9, 29.99),  # just under -> nothing
    ]
    result = generar(construir(extract_sql(people, "test")))
    flags = flags_from_engine(result)
    assert flags == {1: "S1b", 4: "S1b"}
    assert set(result["baseline_fge_menor_60"]) == {2}


def test_survey_variance_hand_computed():
    # 1 stratum, 2 PSUs of 2, equal weights. p = 0.5. z = (y - p)/4 per person; PSU totals: +0.25, -0.25.
    # V = 2/(2-1) * ((0.25)^2 + (-0.25)^2) = 0.25 -> SE = 0.5 (on the proportion scale)
    est = survey_proportion([1, 1, 0, 0], [1] * 4, [1.0] * 4, [1] * 4, [1, 1, 2, 2])
    assert est.p == pytest.approx(0.5)
    assert est.df == 1
    se_logit = 0.5 / 0.25
    import math
    assert est.hi == pytest.approx(1 / (1 + math.exp(-est.t * se_logit)))


def test_single_psu_stratum_is_refused():
    with pytest.raises(ValueError):
        survey_proportion([1, 0, 1], [1, 1, 1], [1.0] * 3, [1, 1, 2], [1, 2, 1])
