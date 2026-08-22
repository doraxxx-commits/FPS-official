"""
LeagueSystem — piramida lig w obrębie jednego kraju (punkt 27 Game Planu).

"Ekstraklasa -> spadek -> 1 Liga -> awans -> 2 Liga -> awans [...] Ale nie
tylko gracz ma awansować. Cały świat ma się zmieniać." — dlatego awanse i
spadki działają na WSZYSTKIE kluby w systemie na podstawie końcowej tabeli,
a nie tylko na klub gracza.
"""

from __future__ import annotations

from football_engine.season.standings import StandingsRow
from football_engine.world.league import League


class LeagueSystem:
    """Uporządkowana od najwyższego do najniższego poziomu piramida lig."""

    def __init__(
        self,
        country: str,
        leagues: list[League],
        promotion_count: int = 2,
        relegation_count: int = 2,
    ) -> None:
        """
        Args:
            leagues: ligi w kolejności od najwyższego poziomu (tier 0) w dół.
            promotion_count / relegation_count: liczba klubów wymieniana
                między sąsiednimi poziomami na koniec sezonu. Domyślnie równe,
                żeby liczebność każdej ligi nie dryfowała w czasie — użycie
                różnych wartości jest możliwe, ale to odpowiedzialność
                wywołującego, żeby ligi nie zaczęły się kurczyć/puchnąć.
        """
        if len(leagues) < 1:
            raise ValueError("LeagueSystem musi mieć co najmniej jedną ligę")

        self.country = country
        self.leagues = leagues
        self.promotion_count = promotion_count
        self.relegation_count = relegation_count

    def apply_promotion_relegation(
        self, tables_by_tier: dict[int, list[StandingsRow]]
    ) -> list[str]:
        """
        Przenosi kluby między sąsiednimi poziomami na podstawie końcowych
        tabel (punkt 27). `tables_by_tier` to tabela per indeks poziomu
        (0 = najwyższy), zwykle wyliczona przez `SeasonEngine.get_table()`
        dla każdej ligi.

        Returns:
            Lista komunikatów do logu/mediów (punkt 35: "News").
        """
        logs: list[str] = []

        for tier in range(len(self.leagues) - 1):
            upper = self.leagues[tier]
            lower = self.leagues[tier + 1]
            upper_table = tables_by_tier[tier]
            lower_table = tables_by_tier[tier + 1]

            relegated = [row.club for row in upper_table[-self.relegation_count:]]
            promoted = [row.club for row in lower_table[: self.promotion_count]]

            for club in relegated:
                upper.clubs.remove(club)
                lower.clubs.append(club)
                logs.append(f"🔴 {club.name} spada z {upper.name} do {lower.name}")

            for club in promoted:
                lower.clubs.remove(club)
                upper.clubs.append(club)
                logs.append(f"🟢 {club.name} awansuje z {lower.name} do {upper.name}")

        return logs

    def all_clubs(self) -> list:
        """Wszystkie kluby w całym systemie lig — przydatne np. jako pula
        dla AI transferowego (Etap 4), które nie powinno ograniczać się do
        jednej ligi."""
        return [club for league in self.leagues for club in league.clubs]

    def __repr__(self) -> str:
        tiers = ", ".join(f"{l.name} ({len(l.clubs)})" for l in self.leagues)
        return f"<LeagueSystem {self.country}: {tiers}>"
