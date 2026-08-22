"""
Silnik czasu (punkt 52 Game Planu: "Świat musi żyć podczas symulacji").

Etap 1 reprezentował czas jako sezon + numer kolejki. Etap 4 dokłada
prawdziwą datę kalendarzową (punkt 18: "To musi być prawdziwy kalendarz,
a nie tylko zmienna week") — potrzebną do tego, żeby okna transferowe
miały realne zakresy dat (1 lipca-31 sierpnia, 1-31 stycznia), a nie
umowny numer tygodnia.
"""

from __future__ import annotations

import datetime


class GameCalendar:
    """Śledzi bieżący sezon, kolejkę rozgrywek i realną datę w grze."""

    def __init__(
        self,
        start_season: str = "2026/27",
        start_date: datetime.date | None = None,
    ) -> None:
        self.season = start_season
        self.matchday = 1
        self.current_date = start_date or datetime.date(
            int(start_season.split("/")[0]), 7, 1
        )

    def advance_matchday(self) -> None:
        """Przechodzi do kolejnej kolejki (odpowiednik jednego tygodnia w grze)."""
        self.matchday += 1
        self.current_date += datetime.timedelta(days=7)

    def advance_days(self, days: int) -> None:
        """Przesuwa samą datę (np. tygodnie przerwy międzysezonowej, okno transferowe)."""
        self.current_date += datetime.timedelta(days=days)

    def advance_season(self) -> None:
        """Kończy bieżący sezon i przechodzi do następnego (np. 2026/27 -> 2027/28),
        przeskakując datę do 1 lipca kolejnego roku (start letniego okna)."""
        start_year_str, _ = self.season.split("/")
        next_start = int(start_year_str) + 1
        self.season = f"{next_start}/{str(next_start + 1)[-2:]}"
        self.matchday = 1
        self.current_date = datetime.date(next_start, 7, 1)

    def __repr__(self) -> str:
        return (
            f"<GameCalendar sezon={self.season}, kolejka={self.matchday}, "
            f"data={self.current_date.isoformat()}>"
        )

