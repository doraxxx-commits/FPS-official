"""
League — pojedyncza liga/rozgrywki (np. Ekstraklasa).

W Etapie 1 liga to po prostu zbiór klubów + metadane. Awanse/spadki
między ligami (Game Plan pkt 27) dojdą w Etapie 5 (Świat), kiedy
będzie istniało więcej niż jedna liga w hierarchii jednego kraju.
"""

from __future__ import annotations

from football_engine.world.club import Club


class League:
    """Rozgrywki ligowe grupujące kluby."""

    def __init__(self, name: str, country: str, clubs: list[Club]) -> None:
        if len(clubs) < 2:
            raise ValueError("Liga musi mieć co najmniej 2 kluby")

        self.name = name
        self.country = country
        self.clubs = clubs

    def get_club(self, club_id: str) -> Club:
        for club in self.clubs:
            if club.id == club_id:
                return club
        raise KeyError(f"Nie znaleziono klubu o id={club_id} w lidze {self.name}")

    def reset_season(self) -> None:
        """Zeruje statystyki wszystkich klubów na starcie nowego sezonu."""
        for club in self.clubs:
            club.reset_season_stats()

    def __repr__(self) -> str:
        return f"<League {self.name} ({self.country}), {len(self.clubs)} klubów>"
