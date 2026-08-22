"""
Kontuzje (punkt 11 Game Planu).

Ryzyko kontuzji rośnie, gdy kondycja zawodnika jest niska (punkt 10:
"Jeżeli grasz dalej: Ryzyko kontuzji wzrosło.") — mechanika łącząca
zmęczenie z kontuzjami zamiast czysto losowego zdarzenia w tle.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class InjuryType:
    name: str
    min_weeks: int
    max_weeks: int
    ovr_impact: int  # tymczasowy spadek OVR/formy w trakcie rekonwalescencji


INJURY_TYPES: list[InjuryType] = [
    InjuryType("Stłuczenie", 1, 2, ovr_impact=2),
    InjuryType("Skręcenie kostki", 2, 4, ovr_impact=4),
    InjuryType("Naciągnięty mięsień", 3, 5, ovr_impact=5),
    InjuryType("Uraz więzadeł", 6, 10, ovr_impact=8),
    InjuryType("Uraz kolana", 8, 16, ovr_impact=10),
]


class Injury:
    """Aktywna kontuzja konkretnego zawodnika."""

    def __init__(self, injury_type: InjuryType, weeks_out: int) -> None:
        self.name = injury_type.name
        self.ovr_impact = injury_type.ovr_impact
        self.total_weeks = weeks_out
        self.weeks_remaining = weeks_out

    @property
    def is_healed(self) -> bool:
        return self.weeks_remaining <= 0

    def advance_week(self) -> None:
        self.weeks_remaining = max(0, self.weeks_remaining - 1)

    def __repr__(self) -> str:
        return f"<Injury {self.name}, pozostało {self.weeks_remaining}/{self.total_weeks} tyg.>"


def _injury_probability(condition: int) -> float:
    """
    Prawdopodobieństwo kontuzji po meczu, w zależności od kondycji.

    Przy pełnej kondycji (100) ryzyko jest niskie (bazowe ~1.5%).
    Poniżej ~50 kondycji ryzyko rośnie wyraźnie — to ma zniechęcać
    do grania "na oporach" bez odpoczynku.
    """
    base_risk = 0.015
    if condition >= 70:
        return base_risk
    fatigue_factor = (70 - condition) / 70  # 0.0 przy 70, 1.0 przy 0
    return base_risk + fatigue_factor * 0.12  # do ~13.5% ryzyka przy condition=0


def check_for_injury(condition: int, rng: random.Random | None = None) -> Injury | None:
    """Sprawdza, czy po meczu dochodzi do kontuzji. Zwraca Injury albo None."""
    rng = rng or random.Random()
    if rng.random() >= _injury_probability(condition):
        return None

    injury_type = rng.choice(INJURY_TYPES)
    weeks_out = rng.randint(injury_type.min_weeks, injury_type.max_weeks)
    return Injury(injury_type, weeks_out)
