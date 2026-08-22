"""
Tabela ligowa (punkt 26 Game Planu: "Tabela ma być żywa").

W Etapie 1 tabela jest wyliczana na żądanie na podstawie statystyk
klubów (Club.points, Club.goal_difference itd.) — same statystyki
są aktualizowane przez SeasonEngine po każdym meczu.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_engine.world.club import Club
    from football_engine.world.league import League


@dataclass(frozen=True)
class StandingsRow:
    position: int
    club: Club

    def __repr__(self) -> str:
        c = self.club
        return (
            f"{self.position:>2}. {c.name:<20} "
            f"M:{c.played:<3} W:{c.wins:<3} R:{c.draws:<3} P:{c.losses:<3} "
            f"+/-:{c.goal_difference:+d} PKT:{c.points}"
        )


def build_table(league: League) -> list[StandingsRow]:
    """
    Buduje posortowaną tabelę ligową.

    Kolejność sortowania: punkty (malejąco) -> różnica bramek (malejąco)
    -> bramki strzelone (malejąco) -> nazwa klubu (alfabetycznie, jako
    stabilny tie-breaker zanim dojdzie np. mecz bezpośredni w kolejnym etapie).
    """
    sorted_clubs = sorted(
        league.clubs,
        key=lambda c: (-c.points, -c.goal_difference, -c.goals_for, c.name),
    )
    return [StandingsRow(position=i + 1, club=club) for i, club in enumerate(sorted_clubs)]


def print_table(league: League) -> None:
    """Wypisuje tabelę do konsoli — pomocnicze do debugowania/demo."""
    print(f"\n=== TABELA: {league.name} ({league.country}) ===")
    print(f"{'#':>2}  {'Klub':<20} {'M':<4}{'W':<4}{'R':<4}{'P':<4}{'+/-':<6}PKT")
    for row in build_table(league):
        c = row.club
        print(
            f"{row.position:>2}. {c.name:<20} "
            f"{c.played:<4}{c.wins:<4}{c.draws:<4}{c.losses:<4}"
            f"{c.goal_difference:<+6}{c.points}"
        )
