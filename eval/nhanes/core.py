"""NHANES external evaluation: pure functions (no network, no pandas at import time).

Protocol: docs/EVAL_PROTOCOL.md (signed 15 Nov 2026). Nothing here changes rules/: the engine runs unmodified.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

# Fixed dates for the one-visit mapping (NHANES does not publish exam dates).
EXAM_DATE = "2025-01-15"
REFERENCE_DATE = "2025-08-15"   # exam + 7 months: "an abnormal result nobody has repeated yet"
EXAM_YEAR = 2025

LOINC_EGFR_2021 = "98979-8"
LOINC_ACR_MG_G = "9318-7"
MALE, FEMALE = 8507, 8532       # OMOP gender_concept_id


def egfr_ckd_epi_2021(scr_mg_dl: float, age: float, female: bool) -> float:
    """CKD-EPI 2021 creatinine equation, race-free (Inker et al., NEJM 2021; doi:10.1056/NEJMoa2102953).

    eGFR = 142 * min(Scr/K, 1)^a * max(Scr/K, 1)^-1.200 * 0.9938^age * 1.012 [female]
    K = 0.7 (F) / 0.9 (M); a = -0.241 (F) / -0.302 (M). Formula as published by the NKF (kidney.org, read 15 Nov 2026).
    """
    if scr_mg_dl is None or scr_mg_dl <= 0 or age is None:
        raise ValueError("serum creatinine must be > 0 and age present")
    k, a = (0.7, -0.241) if female else (0.9, -0.302)
    r = scr_mg_dl / k
    egfr = 142.0 * min(r, 1.0) ** a * max(r, 1.0) ** -1.200 * 0.9938 ** age
    return egfr * 1.012 if female else egfr


@dataclass(frozen=True)
class Participant:
    seqn: int
    age: float
    female: bool
    diabetes: bool
    hypertension: bool
    scr: float          # mg/dL
    acr: float          # mg/g, first (or only) urine
    weight: float
    stratum: int
    psu: int
    acr2: Optional[float] = None   # mg/g, second urine (NHANES 2009-2010 only)

    @property
    def egfr(self) -> float:
        return egfr_ckd_epi_2021(self.scr, self.age, self.female)


def extract_sql(people: Iterable[Participant], source: str) -> str:
    """One-visit extract in the repo's OMOP-shaped schema (data/schema.sql). Numbers only; no free text."""
    p_rows, c_rows, m_rows = [], [], []
    cid = mid = 0
    for p in people:
        sex = FEMALE if p.female else MALE
        p_rows.append(f"({p.seqn}, {sex}, {EXAM_YEAR - int(p.age)}, 0, 0, 'NHANES {p.seqn}', '{'F' if p.female else 'M'}')")
        for flag, code in ((p.diabetes, "E11"), (p.hypertension, "I10")):
            if flag:
                cid += 1
                c_rows.append(f"({cid}, {p.seqn}, 0, '2020-01-01', 0, '{code}')")
        mid += 1
        m_rows.append(f"({mid}, {p.seqn}, 0, '{EXAM_DATE}', 0, {round(p.egfr, 1)}, 'mL/min/1.73m2', '{LOINC_EGFR_2021}')")
        mid += 1
        m_rows.append(f"({mid}, {p.seqn}, 0, '{EXAM_DATE}', 0, {round(p.acr, 2)}, 'mg/g', '{LOINC_ACR_MG_G}')")
    parts = [f"INSERT INTO extract_meta VALUES (1, '{REFERENCE_DATE}', 1, '{source}');"]
    if p_rows:
        parts.append("INSERT INTO person (person_id, gender_concept_id, year_of_birth, race_concept_id, "
                     "ethnicity_concept_id, person_source_value, gender_source_value) VALUES\n" + ",\n".join(p_rows) + ";")
    if c_rows:
        parts.append("INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, "
                     "condition_start_date, condition_type_concept_id, condition_source_value) VALUES\n"
                     + ",\n".join(c_rows) + ";")
    if m_rows:
        parts.append("INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, "
                     "measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value) VALUES\n"
                     + ",\n".join(m_rows) + ";")
    return "\n".join(parts) + "\n"


@dataclass(frozen=True)
class Estimate:
    p: float
    lo: float
    hi: float
    n: int          # unweighted participants in the domain
    events: int     # unweighted participants with y = 1
    df: int = 0     # design degrees of freedom (#PSU - #strata)
    t: float = 0.0  # t quantile used for the 95 % CI

    def per_1000(self) -> Dict[str, float]:
        return {"per_1000": round(self.p * 1000, 1), "ci95_lo": round(self.lo * 1000, 1),
                "ci95_hi": round(self.hi * 1000, 1), "n": self.n, "events": self.events,
                "df": self.df, "t": round(self.t, 4)}


def _t_quantile(df: int) -> float:
    """Exact t quantile (scipy, requirements-eval.txt). Without scipy: 1.96, and the value is written to the output."""
    try:
        from scipy.stats import t
        return float(t.ppf(0.975, df))
    except ImportError:  # CI unit tests do not install scipy; run.py refuses to run without it
        return 1.96


def survey_proportion(y: Sequence[int], domain: Sequence[int], w: Sequence[float],
                      stratum: Sequence[int], psu: Sequence[int]) -> Estimate:
    """Weighted proportion of y within a domain, with Taylor-linearised variance (strata + PSU, with replacement).

    The whole sample is passed so that PSUs with no domain members still count (correct domain estimation).
    95 % CI on the logit scale, t with df = #PSU - #strata (NCHS practice for NHANES).
    """
    sw = sum(wi * di for wi, di in zip(w, domain))
    if sw <= 0:
        raise ValueError("empty domain")
    p = sum(wi * di * yi for wi, di, yi in zip(w, domain, y)) / sw
    totals: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for wi, di, yi, h, j in zip(w, domain, y, stratum, psu):
        totals[h][j] += wi * di * (yi - p) / sw
    var = 0.0
    for psus in totals.values():
        vals = list(psus.values())
        nh = len(vals)
        if nh < 2:
            raise ValueError("a stratum has a single PSU: its variance cannot be estimated (collapse strata first)")
        mean = sum(vals) / nh
        var += nh / (nh - 1) * sum((v - mean) ** 2 for v in vals)
    df = max(1, sum(len(v) for v in totals.values()) - len(totals))
    n = sum(1 for d in domain if d)
    events = sum(1 for d, yi in zip(domain, y) if d and yi)
    t = _t_quantile(df)
    if p <= 0 or p >= 1 or var == 0:
        return Estimate(p, p, p, n, events, df, t)
    se_logit = math.sqrt(var) / (p * (1 - p))
    logit = math.log(p / (1 - p))
    inv = lambda x: 1 / (1 + math.exp(-x))  # noqa: E731
    return Estimate(p, inv(logit - t * se_logit), inv(logit + t * se_logit), n, events, df, t)


def in_population(age, pregnant, diabetes, hypertension, scr, acr, weight) -> bool:
    """Protocol population: adult, diabetes or hypertension, not pregnant, both labs present, MEC weight > 0."""
    return (age is not None and age >= 18 and not pregnant and (diabetes or hypertension)
            and scr is not None and scr > 0 and acr is not None and weight is not None and weight > 0)


def flags_from_engine(result: dict) -> Dict[int, str]:
    """person_id -> main rule of the order the engine prepared (S1a / S1b / S3 / S3c...)."""
    return {p["person_id"]: p["regla"] for p in result["pedidos"]}


def baseline_ids(result: dict) -> List[int]:
    return list(result["baseline_fge_menor_60"])
