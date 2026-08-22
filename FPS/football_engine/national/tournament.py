"""
InternationalTournament — EURO / Mistrzostwa Świata (punkt 39 Game Planu).

Format: faza grupowa (pojedynczy "każdy z każdym" w każdej grupie) ->
najlepsze drużyny z każdej grupy przechodzą do fazy pucharowej, gdzie
reużywamy `CupEngine` z Etapu 6 zamiast pisać osobny silnik knockout —
mechanika "kolejne rundy do finału" jest identyczna dla klubów i reprezentacji.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from football_engine.cup.cup_engine import CupEngine
from football_engine.match.simulation import simulate_match
from football_engine.season.fixtures import generate_single_round_robin

if TYPE_CHECKING:
    from football_engine.national.national_team import NationalTeam


class InternationalTournament:
    """Rozgrywa pełny turniej: grupy -> faza pucharowa -> mistrz."""

    def __init__(
        self,
        name: str,
        groups: list[list["NationalTeam"]],
        teams_advancing_per_group: int = 2,
        rng: random.Random | None = None,
    ) -> None:
        if any(len(group) % 2 != 0 for group in groups):
            raise ValueError(
                "Każda grupa musi mieć parzystą liczbę drużyn (ograniczenie "
                "generatora terminarza — patrz season/fixtures.py)"
            )

        self.name = name
        self.groups = groups
        self.teams_advancing_per_group = teams_advancing_per_group
        self.rng = rng or random.Random()

        self.group_standings: dict[int, list["NationalTeam"]] = {}
        self.knockout: CupEngine | None = None
        self.champion: "NationalTeam | None" = None

    def play_group_stage(self) -> dict[int, list["NationalTeam"]]:
        """Rozgrywa fazę grupową i zwraca posortowane tabele per grupa (indeks 0, 1, ...)."""
        for group_index, group in enumerate(self.groups):
            for team in group:
                team.reset_stats()

            fixtures = generate_single_round_robin(group)
            for fixture in fixtures:
                result = simulate_match(fixture.home, fixture.away, rng=self.rng)
                fixture.home.register_result(result.home_goals, result.away_goals)
                fixture.away.register_result(result.away_goals, result.home_goals)

            sorted_group = sorted(
                group,
                key=lambda t: (-t.points, -t.goal_difference, -t.goals_for, t.name),
            )
            self.group_standings[group_index] = sorted_group

        return self.group_standings

    def play_knockout_stage(self) -> "NationalTeam":
        """Rozgrywa fazę pucharową spośród drużyn awansujących z grup i zwraca mistrza."""
        if not self.group_standings:
            raise RuntimeError("Najpierw rozegraj fazę grupową (play_group_stage)")

        advancing: list["NationalTeam"] = []
        for sorted_group in self.group_standings.values():
            advancing.extend(sorted_group[: self.teams_advancing_per_group])

        self.knockout = CupEngine(f"{self.name} — faza pucharowa", advancing, two_legged=False, rng=self.rng)
        self.champion = self.knockout.play_until_final()
        return self.champion

    def run_full_tournament(self) -> "NationalTeam":
        self.play_group_stage()
        return self.play_knockout_stage()

    def __repr__(self) -> str:
        status = f"mistrz={self.champion.name}" if self.champion else "w trakcie"
        return f"<InternationalTournament {self.name}, {status}>"
