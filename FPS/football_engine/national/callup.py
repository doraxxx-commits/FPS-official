"""
Powołania do reprezentacji (punkt 38 Game Planu).

Wybór jest prosty (najlepsi wg OVR spośród uprawnionych) — bardziej
złożone kryteria (forma, kondycja, styl trenera) już istnieją w
`club/squad.py` i będą stosowane przy wyborze SKŁADU NA MECZ reprezentacji
(punkt 40 dojdzie razem z integracją kariery gracza) — tutaj chodzi tylko
o to, kto w ogóle dostaje powołanie do szerokiej kadry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from football_engine.national.national_team import TIER_MAX_AGE, NationalTeamTier

if TYPE_CHECKING:
    from football_engine.career.player import Player

_DEFAULT_SQUAD_SIZE = 23


def is_eligible(player: "Player", country: str, tier: NationalTeamTier) -> bool:
    """Sprawdza, czy zawodnik może być powołany na dany szczebel reprezentacji."""
    if player.country != country:
        return False
    return player.age <= TIER_MAX_AGE[tier]


def call_up_squad(
    tier: NationalTeamTier,
    country: str,
    player_pool: list["Player"],
    squad_size: int = _DEFAULT_SQUAD_SIZE,
) -> list["Player"]:
    """
    Wybiera najlepszą dostępną kadrę (do `squad_size` zawodników) spośród
    uprawnionych, zdrowych zawodników — posortowanych wg OVR malejąco.
    """
    eligible = [
        p for p in player_pool
        if is_eligible(p, country, tier) and not p.is_injured
    ]
    eligible.sort(key=lambda p: p.ovr, reverse=True)
    return eligible[:squad_size]
