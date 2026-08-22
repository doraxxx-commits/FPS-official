"""
Wycena wartości rynkowej zawodnika.

Nie ma tego jako osobnego punktu w Game Planie, ale jest niezbędna, żeby
oferty transferowe (17), AI klubów (19-21) i wypożyczenia (22) miały się
do czego odnosić. Model: baza rosnąca wykładniczo z OVR (tak jak na
realnym rynku transferowym różnica między 70 a 80 OVR znaczy dużo więcej
niż między 50 a 60), modyfikowana wiekiem (szczyt wartości ~24-26 lat)
i premią za potencjał (młody zawodnik z dużą "przestrzenią do rozwoju"
jest wart więcej niż rówieśnik o tym samym OVR, ale niższym suficie).
"""

from __future__ import annotations

from football_engine.career.player import Player

_BASE = 1000
_GROWTH_RATE = 1.13


def _age_multiplier(age: int) -> float:
    if age <= 20:
        return 1.25
    if age <= 26:
        return 1.5  # szczyt wartości rynkowej — najwięcej lat kariery przed sobą
    if age <= 29:
        return 1.1
    if age <= 32:
        return 0.7
    if age <= 35:
        return 0.4
    return 0.2


def estimate_market_value(player: Player) -> int:
    """Szacuje wartość rynkową zawodnika na podstawie OVR, wieku i potencjału."""
    base = _BASE * (_GROWTH_RATE ** player.ovr)
    base *= _age_multiplier(player.age)

    if player.potential > player.ovr:
        gap = player.potential - player.ovr
        base *= 1 + min(0.5, gap * 0.015)

    return round(base)
