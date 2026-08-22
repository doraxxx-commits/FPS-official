"""
Losowanie drabinki pucharowej (punkt 37 Game Planu: "losowanie, kolejne
rundy, finał").

Puchar Polski w prawdziwym formacie losuje pary na nowo przed każdą rundą
(nie trzyma sztywnej drabinki turniejowej jak np. tenis) — dlatego
`cup_engine.py` wywołuje `draw_round()` osobno na starcie każdej rundy,
zamiast ustalać całą drabinkę raz na starcie turnieju.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_engine.world.club import Club


@dataclass
class Tie:
    """Pojedyncza para w rundzie pucharowej. `away` = None oznacza wolny los (bye)."""

    round_name: str
    home: "Club"
    away: "Club | None"


def draw_round(clubs: list["Club"], round_name: str, rng: random.Random | None = None) -> list[Tie]:
    """
    Losuje pary na jedną rundę pucharu. Przy nieparzystej liczbie klubów
    jeden losowo wybrany klub dostaje wolny los (awansuje bez gry).
    """
    rng = rng or random.Random()
    pool = list(clubs)
    rng.shuffle(pool)

    ties: list[Tie] = []

    if len(pool) % 2 == 1:
        bye_club = pool.pop()
        ties.append(Tie(round_name=round_name, home=bye_club, away=None))

    for i in range(0, len(pool), 2):
        ties.append(Tie(round_name=round_name, home=pool[i], away=pool[i + 1]))

    return ties


def round_name_for(clubs_remaining: int) -> str:
    """Nazwa rundy na podstawie liczby klubów WCHODZĄCYCH do danej rundy."""
    names = {
        2: "Finał",
        4: "Półfinał",
        8: "Ćwierćfinał",
        16: "1/8 finału",
        32: "1/16 finału",
        64: "1/32 finału",
    }
    return names.get(clubs_remaining, f"Runda ({clubs_remaining} klubów)")
