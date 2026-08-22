"""
SeasonEngine — serce Etapu 1.

Łączy terminarz (fixtures.py), symulację meczu (match/simulation.py)
i tabelę (standings.py) w jeden spójny cykl sezonu.

Celowo NIE wie nic o graczu/karierze — to jest czysto silnik świata
(punkt 52: "świat ma żyć również bez gracza"). Warstwa kariery, która
w Etapie 2+ będzie decydować "ten jeden mecz gracz rozgrywa interaktywnie,
resztę symulujemy", zostanie zbudowana NAD tym silnikiem, wywołując
`simulate_matchday()` kolejka po kolejce i w razie potrzeby podmieniając
wynik meczu gracza wynikiem z interaktywnego match engine (Etap 6).
Dzięki temu SeasonEngine pozostaje przydatny w każdym z 3 trybów
(pkt 2-4 Game Planu), zamiast być pisany pod jeden konkretny tryb.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from football_engine.match.simulation import MatchResult, simulate_match
from football_engine.season.fixtures import Fixture, generate_double_round_robin
from football_engine.season.standings import StandingsRow, build_table

if TYPE_CHECKING:
    from football_engine.world.league import League


class SeasonEngine:
    """Zarządza jednym pełnym sezonem ligowym."""

    def __init__(self, league: League, rng: random.Random | None = None) -> None:
        self.league = league
        self.rng = rng or random.Random()
        self.fixtures: list[Fixture] = generate_double_round_robin(league.clubs)
        self.results: list[MatchResult] = []
        self._current_matchday = 1
        self._total_matchdays = max(f.matchday for f in self.fixtures)

    @property
    def total_matchdays(self) -> int:
        return self._total_matchdays

    @property
    def current_matchday(self) -> int:
        return self._current_matchday

    def is_finished(self) -> bool:
        return self._current_matchday > self._total_matchdays

    def get_fixtures(self, matchday: int) -> list[Fixture]:
        """Zwraca zaplanowane mecze danej kolejki (bez ich rozgrywania)."""
        return [f for f in self.fixtures if f.matchday == matchday]

    def simulate_matchday(self, matchday: int | None = None) -> list[MatchResult]:
        """
        Symuluje wszystkie mecze danej kolejki i aktualizuje statystyki klubów.

        Args:
            matchday: numer kolejki do rozegrania. Jeśli None, rozgrywana jest
                bieżąca kolejka (`current_matchday`) i licznik przesuwa się dalej —
                to jest ścieżka używana do sekwencyjnego przechodzenia przez sezon
                (Tryb 2 z Game Planu).

        Returns:
            Lista wyników meczów tej kolejki.
        """
        target_matchday = matchday if matchday is not None else self._current_matchday
        matchday_fixtures = self.get_fixtures(target_matchday)

        matchday_results = []
        for fixture in matchday_fixtures:
            result = simulate_match(fixture.home, fixture.away, rng=self.rng)
            fixture.home.register_result(result.home_goals, result.away_goals)
            fixture.away.register_result(result.away_goals, result.home_goals)
            matchday_results.append(result)

        self.results.extend(matchday_results)

        if matchday is None:
            self._current_matchday += 1

        return matchday_results

    def simulate_remaining_season(self) -> list[MatchResult]:
        """
        Symuluje wszystkie pozostałe kolejki na raz (Tryb 3: "Symuluj sezon").

        Rozgrywa je jednak sekwencyjnie kolejka po kolejce (nie jednym losowaniem
        końcowego wyniku zawodnika) — patrz punkt 4 Game Planu, gdzie krytykowany
        jest właśnie stary silnik losujący wynik sezonu z góry.
        """
        all_results: list[MatchResult] = []
        while not self.is_finished():
            all_results.extend(self.simulate_matchday())
        return all_results

    def get_table(self) -> list[StandingsRow]:
        return build_table(self.league)

    def reset_for_new_season(self) -> None:
        """
        Przygotowuje ligę do nowego sezonu:
        - Postarza wszystkich piłkarzy w klubach o +1 rok
        - Sprawia, że najstarsi przechodzą na emeryturę
        - Generuje nowy terminarz i czyści dotychczasowe mecze
        """
        # 1. Postarzanie zawodników i zmiana OVR w kadrach klubów
        for club in self.league.clubs:
            if hasattr(club, 'squad'):
                for player in club.squad:
                    if hasattr(player, 'age_up'):
                        player.age_up(1)
                    else:
                        player.age += 1
                    
                    if hasattr(player, 'recalculate_ovr'):
                        player.recalculate_ovr()

            if hasattr(club, 'reset_season_stats'):
                club.reset_season_stats()

        # 2. Generowanie nowego terminarza meczów
        self.fixtures = generate_double_round_robin(self.league.clubs)
        self.results.clear()
        self._current_matchday = 1
        self._total_matchdays = max(f.matchday for f in self.fixtures)
