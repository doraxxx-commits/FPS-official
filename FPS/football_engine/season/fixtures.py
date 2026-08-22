"""
Generowanie terminarza sezonu.

Punkt 24 Game Planu: "Każdy sezon ma prawdziwy terminarz [...] Nie chcemy
losowania 'następnego meczu' bez rzeczywistej struktury sezonu."

Ten moduł buduje pełny, ustalony z góry harmonogram kolejek (metoda
"circle method"), zamiast losować mecze na bieżąco. Dla N klubów
generowana jest runda zasadnicza (N-1 kolejek) i rewanżowa (kolejne
N-1 kolejek, z odwróconymi gospodarzami) — czyli standardowy układ
ligowy "każdy z każdym dwukrotnie".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Tylko do podpowiedzi typów — patrz analogiczny komentarz w club/squad.py
    # o unikaniu cyklu importów world <-> season.
    from football_engine.world.club import Club


@dataclass(frozen=True)
class Fixture:
    matchday: int
    home: Club
    away: Club
    played: bool = False


def _generate_single_leg_rounds(clubs: list[Club]) -> list[Fixture]:
    """Generuje N-1 kolejek pojedynczego 'każdy z każdym' metodą circle method
    — współdzielone przez `generate_double_round_robin` (runda zasadnicza)
    i `generate_single_round_robin` (np. faza grupowa reprezentacji, punkt 39)."""
    if len(clubs) % 2 != 0:
        raise ValueError(
            "Generator terminarza obsługuje tylko parzystą liczbę drużyn "
            "(obsługa 'wolnego losu' dla nieparzystej liczby dojdzie później)"
        )

    n = len(clubs)
    rotation = list(clubs)
    fixtures: list[Fixture] = []

    rounds = n - 1
    for round_index in range(rounds):
        for i in range(n // 2):
            home = rotation[i]
            away = rotation[n - 1 - i]
            if round_index % 2 == 1:
                home, away = away, home
            fixtures.append(Fixture(matchday=round_index + 1, home=home, away=away))
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

    return fixtures


def generate_single_round_robin(clubs: list[Club]) -> list[Fixture]:
    """
    Generuje terminarz pojedynczego "każdy z każdym" (N-1 kolejek) — np. na
    potrzeby fazy grupowej turnieju reprezentacji (punkt 39), gdzie drużyny
    grają każda z każdą tylko raz, a nie dwukrotnie jak w lidze.
    """
    return _generate_single_leg_rounds(clubs)


def generate_double_round_robin(clubs: list[Club]) -> list[Fixture]:
    """
    Generuje pełny terminarz podwójnego "każdy z każdym".

    Args:
        clubs: lista klubów w lidze (parzysta liczba — dla nieparzystej
            liczby klubów należy dodać "bye"/wolny los, co dojdzie
            w kolejnym etapie razem z obsługą lig o nietypowej wielkości).

    Returns:
        Lista Fixture w kolejności kolejek (matchday 1, 2, 3, ...).
    """
    fixtures = _generate_single_leg_rounds(clubs)
    rounds_in_half = len(clubs) - 1

    # Runda rewanżowa: te same pary, odwrócone gospodarstwo.
    second_half = [
        Fixture(matchday=f.matchday + rounds_in_half, home=f.away, away=f.home)
        for f in fixtures
    ]

    return fixtures + second_half
