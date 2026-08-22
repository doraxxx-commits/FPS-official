"""
Atrybuty zawodnika i wyliczanie OVR.

Punkt 6 Game Planu: różne pozycje mają różny zestaw ważnych umiejętności
(napastnik: finishing/shot_power/positioning..., pomocnik: passing/vision...).
Zamiast osobnej klasy atrybutów na każdą pozycję, używamy jednego wspólnego
zestawu (tak jak w większości gier piłkarskich) i WAŻYMY go inaczej w
zależności od pozycji przy liczeniu OVR — dzięki temu ten sam zawodnik
przesunięty na inną pozycję (np. CM -> CDM) od razu ma inne OVR, bez
przepisywania danych.

Skala: 1-99 (konwencja z gier piłkarskich).
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from football_engine.career.position import Position

_MIN_ATTR = 1
_MAX_ATTR = 99


@dataclass
class Attributes:
    """Wspólny zestaw atrybutów dla wszystkich pozycji (z pominiętymi
    nieistotnymi zerami tam, gdzie dana umiejętność nie ma zastosowania)."""

    # Ogólne / z polem
    pace: int = 50
    acceleration: int = 50
    dribbling: int = 50
    ball_control: int = 50
    passing: int = 50
    vision: int = 50
    technique: int = 50
    positioning: int = 50
    strength: int = 50
    stamina: int = 50

    # Ofensywne
    finishing: int = 50
    shot_power: int = 50
    heading: int = 50

    # Defensywne
    tackling: int = 50
    marking: int = 50

    # Bramkarskie
    reflexes: int = 1
    handling: int = 1
    diving: int = 1
    kicking: int = 1

    def __post_init__(self) -> None:
        self.clamp()

    def clamp(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            clamped = max(_MIN_ATTR, min(_MAX_ATTR, value))
            if clamped != value:
                setattr(self, f.name, clamped)

    def as_dict(self) -> dict[str, int]:
        return {f.name: getattr(self, f.name) for f in fields(self)}


# Waga poszczególnych atrybutów przy liczeniu OVR, per pozycja.
# Wagi sumują się do 1.0 dla każdej pozycji.
POSITION_WEIGHTS: dict[Position, dict[str, float]] = {
    Position.GK: {
        "reflexes": 0.30, "handling": 0.20, "diving": 0.20,
        "kicking": 0.10, "positioning": 0.10, "strength": 0.10,
    },
    Position.CB: {
        "tackling": 0.25, "marking": 0.25, "strength": 0.15,
        "heading": 0.15, "positioning": 0.10, "passing": 0.10,
    },
    Position.LB: {
        "pace": 0.20, "tackling": 0.20, "marking": 0.15,
        "stamina": 0.15, "passing": 0.15, "dribbling": 0.15,
    },
    Position.RB: {
        "pace": 0.20, "tackling": 0.20, "marking": 0.15,
        "stamina": 0.15, "passing": 0.15, "dribbling": 0.15,
    },
    Position.CDM: {
        "tackling": 0.20, "marking": 0.15, "passing": 0.15,
        "positioning": 0.15, "stamina": 0.15, "strength": 0.10, "vision": 0.10,
    },
    Position.CM: {
        "passing": 0.20, "vision": 0.15, "ball_control": 0.15,
        "stamina": 0.15, "dribbling": 0.15, "tackling": 0.10, "positioning": 0.10,
    },
    Position.CAM: {
        "vision": 0.20, "passing": 0.15, "dribbling": 0.20,
        "ball_control": 0.15, "technique": 0.15, "finishing": 0.15,
    },
    Position.LM: {
        "pace": 0.20, "dribbling": 0.20, "passing": 0.15,
        "stamina": 0.15, "ball_control": 0.15, "technique": 0.15,
    },
    Position.RM: {
        "pace": 0.20, "dribbling": 0.20, "passing": 0.15,
        "stamina": 0.15, "ball_control": 0.15, "technique": 0.15,
    },
    Position.LW: {
        "pace": 0.25, "dribbling": 0.20, "technique": 0.15,
        "finishing": 0.15, "ball_control": 0.15, "passing": 0.10,
    },
    Position.RW: {
        "pace": 0.25, "dribbling": 0.20, "technique": 0.15,
        "finishing": 0.15, "ball_control": 0.15, "passing": 0.10,
    },
    Position.ST: {
        "finishing": 0.30, "shot_power": 0.15, "positioning": 0.15,
        "pace": 0.15, "dribbling": 0.10, "heading": 0.10, "strength": 0.05,
    },
}


def calculate_ovr(attributes: Attributes, position: Position) -> int:
    """Liczy OVR jako ważoną średnią atrybutów istotnych dla danej pozycji."""
    weights = POSITION_WEIGHTS[position]
    attr_values = attributes.as_dict()
    weighted_sum = sum(attr_values[attr] * weight for attr, weight in weights.items())
    return round(weighted_sum)
