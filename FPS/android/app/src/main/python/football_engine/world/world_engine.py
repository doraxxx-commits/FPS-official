"""
WorldEngine — orkiestruje cały system lig przez pełny sezon (punkt 52:
"Świat musi żyć podczas symulacji", punkt 60: "Świat nie jest statyczny").

Łączy: SeasonEngine (Etap 1) per liga, LeagueSystem (awanse/spadki) i
ponowne przeliczenie siły klubów po sezonie — dzięki czemu klub, który
sprzedał gwiazdy i spadł, faktycznie staje się słabszy w kolejnym sezonie
(punkt 60: "2026 Legia 72 OVR [...] 2036 Legia 64 OVR — bo sprzedała
gwiazdy, miała słabe transfery, spadła").
"""

from __future__ import annotations

import random

from football_engine.season.season_engine import SeasonEngine
from football_engine.season.standings import StandingsRow
from football_engine.time_engine import GameCalendar
from football_engine.transfer.ai import run_transfer_window
from football_engine.transfer.offer import TransferOffer
from football_engine.world.league_system import LeagueSystem


class WorldEngine:
    """Symuluje cały system lig jednego kraju sezon po sezonie."""

    def __init__(
        self,
        league_system: LeagueSystem,
        calendar: GameCalendar,
        rng: random.Random | None = None,
    ) -> None:
        self.league_system = league_system
        self.calendar = calendar
        self.rng = rng or random.Random()
        self._season_engines: dict[int, SeasonEngine] = self._build_season_engines()

    def _build_season_engines(self) -> dict[int, SeasonEngine]:
        return {
            tier: SeasonEngine(league, rng=self.rng)
            for tier, league in enumerate(self.league_system.leagues)
        }

    def get_table(self, tier: int) -> list[StandingsRow]:
        return self._season_engines[tier].get_table()

    def run_transfer_window(self) -> list[TransferOffer]:
        """Uruchamia rundę AI transferowego na WSZYSTKICH klubach systemu
        (punkt 20: kluby kupują zawodników między sobą, także spoza jednej ligi)."""
        return run_transfer_window(self.league_system.all_clubs(), self.calendar, rng=self.rng)

    def simulate_full_season(self) -> list[str]:
        """
        Rozgrywa do końca sezon we WSZYSTKICH ligach systemu, stosuje
        awanse/spadki, przelicza siłę każdego klubu na podstawie aktualnego
        składu i przechodzi do kolejnego sezonu (nowy terminarz, wyzerowane
        tabele — bo składy lig się zmieniły).

        Returns:
            Lista komunikatów medialnych o awansach/spadkach (punkt 35).
        """
        for engine in self._season_engines.values():
            engine.simulate_remaining_season()

        tables = {tier: engine.get_table() for tier, engine in self._season_engines.items()}
        news = self.league_system.apply_promotion_relegation(tables)

        # Punkt 60: siła klubu ewoluuje wraz ze składem (transfery, rozwój
        # zawodników, awans/spadek) — nie jest już sztywną liczbą.
        for club in self.league_system.all_clubs():
            club.recalculate_strength_from_squad()

        self.calendar.advance_season()
        for league in self.league_system.leagues:
            league.reset_season()

        self._season_engines = self._build_season_engines()
        return news

    def __repr__(self) -> str:
        return f"<WorldEngine {self.league_system.country}, sezon={self.calendar.season}>"
