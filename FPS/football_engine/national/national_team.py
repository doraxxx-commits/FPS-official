"""
NationalTeam — reprezentacja narodowa (punkt 38 Game Planu).

"Kariera może prowadzić: U-19 -> U-21 -> SENIOR." Celowo NIE wymuszamy
sztywnej progresji przez etapy — utalentowany 18-latek może dostać
powołanie od razu do seniorskiej kadry, tak jak w prawdziwym futbolu.
Ograniczenie wiekowe obowiązuje tylko w górę (U19/U21 mają limit wieku),
nie w dół.

Klasa celowo powiela kształt `world.club.Club` (statystyki meczowe, skład,
trener) zamiast po prostu dziedziczyć po Club — reprezentacja i klub to
inne pojęcia domenowe (zawodnik nie jest "kupowany" do kadry, kadra nie
ma budżetu transferowego) i sztuczne dziedziczenie po Club niosłoby ze
sobą pola, które w ogóle nie mają tu sensu. Ten sam kształt pozwala za to
bezpośrednio reużyć `match.simulation.simulate_match` i `club.squad`
(wybór składu, rywalizacja o miejsce) bez żadnych zmian w tamtych modułach.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_engine.career.player import Player
    from football_engine.career.position import Position
    from football_engine.club.manager import Manager


class NationalTeamTier(str, Enum):
    U19 = "U19"
    U21 = "U21"
    SENIOR = "SENIOR"


TIER_MAX_AGE: dict[NationalTeamTier, int] = {
    NationalTeamTier.U19: 19,
    NationalTeamTier.U21: 21,
    NationalTeamTier.SENIOR: 999,  # brak górnego limitu
}


class NationalTeam:
    """Kadra narodowa jednego kraju na jednym szczeblu (U19/U21/SENIOR)."""

    def __init__(self, country: str, tier: NationalTeamTier) -> None:
        self.id = str(uuid.uuid4())
        self.country = country
        self.tier = tier
        self.name = f"{country} {tier.value}"

        self.squad: list["Player"] = []
        self.manager: "Manager | None" = None

        self.reset_stats()

    def reset_stats(self) -> None:
        """Zeruje statystyki turniejowe — wywoływane na starcie fazy grupowej."""
        self.played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    def register_result(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.wins += 1
        elif goals_for == goals_against:
            self.draws += 1
        else:
            self.losses += 1

    @property
    def strength(self) -> int:
        """Siła kadry — średnie OVR najlepszych 18 powołanych (analogicznie
        do `Club.recalculate_strength_from_squad`)."""
        if not self.squad:
            return 50
        best = sorted(self.squad, key=lambda p: p.ovr, reverse=True)[:18]
        avg_ovr = sum(p.ovr for p in best) / len(best)
        return round(max(1, min(100, avg_ovr)))

    def players_at_position(self, position: "Position") -> list["Player"]:
        return [p for p in self.squad if p.position == position]

    def set_manager(self, manager: "Manager") -> None:
        self.manager = manager

    def __repr__(self) -> str:
        return f"<NationalTeam {self.name}, {len(self.squad)} powołanych, siła={self.strength}>"
