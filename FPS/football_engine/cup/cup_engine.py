"""
CupEngine — rozgrywa turniej pucharowy rundę po rundzie (punkt 37).

Obsługuje mecze jednorundowe (typowe dla wczesnych rund Pucharu Polski)
i dwumeczowe (typowe dla europejskich pucharów, punkt 37: "Liga Konferencji,
Liga Europy, Liga Mistrzów") — sterowane flagą `two_legged`.

Remis w meczu/dwumeczu pucharowym musi mieć zwycięzcę (brak remisów w
pucharze) — rozstrzygamy to ważonym losowaniem opartym o siłę drużyn
(odpowiednik dogrywki + rzutów karnych, bez modelowania samych karnych —
to należy do warstwy "polish" w dalszych etapach).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from football_engine.cup.bracket import Tie, draw_round, round_name_for
from football_engine.match.simulation import MatchResult, simulate_match

if TYPE_CHECKING:
    from football_engine.world.club import Club


@dataclass
class TieResult:
    tie: Tie
    winner: "Club"
    legs: list[MatchResult] = field(default_factory=list)
    decided_by_bye: bool = False
    decided_by_tiebreak: bool = False


def _resolve_tiebreak(home: "Club", away: "Club", rng: random.Random) -> "Club":
    """Ważone losowanie zwycięzcy przy remisie — silniejsza drużyna ma
    większą szansę, ale słabsza wciąż może sprawić niespodziankę."""
    total = home.strength + away.strength
    return home if rng.random() < (home.strength / total) else away


def play_tie(tie: Tie, two_legged: bool, rng: random.Random) -> TieResult:
    """Rozgrywa jedną parę (jeden mecz albo dwumecz) i zwraca zwycięzcę."""
    if tie.away is None:
        return TieResult(tie=tie, winner=tie.home, decided_by_bye=True)

    if not two_legged:
        result = simulate_match(tie.home, tie.away, rng=rng)
        if result.home_goals != result.away_goals:
            winner = result.home if result.home_goals > result.away_goals else result.away
            return TieResult(tie=tie, winner=winner, legs=[result])
        winner = _resolve_tiebreak(tie.home, tie.away, rng)
        return TieResult(tie=tie, winner=winner, legs=[result], decided_by_tiebreak=True)

    leg1 = simulate_match(tie.home, tie.away, rng=rng)
    leg2 = simulate_match(tie.away, tie.home, rng=rng)  # rewanż z odwróconymi gospodarzami

    home_aggregate = leg1.home_goals + leg2.away_goals
    away_aggregate = leg1.away_goals + leg2.home_goals

    if home_aggregate != away_aggregate:
        winner = tie.home if home_aggregate > away_aggregate else tie.away
        return TieResult(tie=tie, winner=winner, legs=[leg1, leg2])

    winner = _resolve_tiebreak(tie.home, tie.away, rng)
    return TieResult(tie=tie, winner=winner, legs=[leg1, leg2], decided_by_tiebreak=True)


class CupEngine:
    """Prowadzi turniej pucharowy od pierwszej rundy do finału."""

    def __init__(
        self,
        name: str,
        clubs: list["Club"],
        two_legged: bool = False,
        rng: random.Random | None = None,
    ) -> None:
        if len(clubs) < 2:
            raise ValueError("Puchar wymaga co najmniej 2 klubów")

        self.name = name
        self.two_legged = two_legged
        self.rng = rng or random.Random()

        self._remaining_clubs: list["Club"] = list(clubs)
        self.rounds_played: list[list[TieResult]] = []
        self.champion: "Club | None" = None

    @property
    def is_finished(self) -> bool:
        return self.champion is not None

    def play_next_round(self) -> list[TieResult]:
        """Losuje pary i rozgrywa jedną rundę, zwracając wyniki wszystkich par."""
        if self.is_finished:
            raise RuntimeError(f"Puchar {self.name} został już rozstrzygnięty")

        round_name = round_name_for(len(self._remaining_clubs))
        ties = draw_round(self._remaining_clubs, round_name, rng=self.rng)

        results = [play_tie(tie, self.two_legged, self.rng) for tie in ties]
        self.rounds_played.append(results)

        self._remaining_clubs = [r.winner for r in results]
        if len(self._remaining_clubs) == 1:
            self.champion = self._remaining_clubs[0]

        return results

    def play_until_final(self) -> "Club":
        """Rozgrywa wszystkie pozostałe rundy na raz i zwraca mistrza pucharu."""
        while not self.is_finished:
            self.play_next_round()
        return self.champion

    def __repr__(self) -> str:
        status = f"mistrz={self.champion.name}" if self.champion else f"pozostało {len(self._remaining_clubs)} klubów"
        return f"<CupEngine {self.name}, {status}>"
