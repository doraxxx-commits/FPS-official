"""
Club — reprezentuje klub w świecie gry.

Etap 1 dał klubowi tożsamość, siłę drużyny (do symulacji meczów) i
statystyki tabelowe. Etap 3 dokłada prawdziwy skład zawodników i trenera
(punkty 12-14, 58-59) — `strength` może być teraz wyliczane ze składu
zamiast być ustawianym ręcznie na sztywno.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from football_engine.career.player import Player
    from football_engine.career.position import Position
    from football_engine.club.manager import Manager


class Club:
    """Pojedynczy klub piłkarski w świecie gry."""

    def __init__(
        self,
        name: str,
        country: str,
        strength: int,
        transfer_budget: float = 0.0,
        colors: list[str] | None = None,
    ) -> None:
        """
        Args:
            name: Nazwa klubu, np. "Legia Warszawa".
            country: Kraj klubu, np. "Polska".
            strength: Siła drużyny w skali 1-100 (używana m.in. do symulacji).
            transfer_budget: Dostępny budżet transferowy dla AI.
            colors: Lista kodów HEX głównych barw klubu, np. ["#005CA9", "#FFFFFF"].
        """
        if not (1 <= strength <= 100):
            raise ValueError("strength musi być w zakresie 1-100")

        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.country: str = country
        self.strength: int = strength
        self.transfer_budget: float = transfer_budget
        self.colors: list[str] = colors if colors is not None else ["#005CA9", "#FFFFFF"]

        self.squad: list[Player] = []
        self.manager: Manager | None = None

        # Statystyki sezonowe
        self.played: int = 0
        self.wins: int = 0
        self.draws: int = 0
        self.losses: int = 0
        self.goals_for: int = 0
        self.goals_against: int = 0

        self.reset_season_stats()

    def add_player(self, player: Player) -> None:
        """Dodaje zawodnika do składu klubu (zapobiega dublowaniu)."""
        if not any(getattr(p, "id", None) == getattr(player, "id", None) for p in self.squad):
            self.squad.append(player)

    def remove_player(self, player_id: str) -> Player | None:
        """Usuwa zawodnika ze składu po jego ID i go zwraca."""
        for i, player in enumerate(self.squad):
            if getattr(player, "id", None) == player_id:
                return self.squad.pop(i)
        return None

    def set_manager(self, manager: Manager) -> None:
        """Przypisuje menedżera do klubu."""
        self.manager = manager

    def players_at_position(self, position: Position | str) -> list[Player]:
        """Zwraca zawodników grających na danej pozycji."""
        target_pos = getattr(position, "value", position)
        return [
            p for p in self.squad 
            if getattr(getattr(p, "position", None), "value", getattr(p, "position", None)) == target_pos
        ]

    def recalculate_strength_from_squad(self, top_n: int = 18) -> None:
        """
        Przelicza `strength` klubu jako średnie OVR najlepszych `top_n`
        zawodników w składzie. Odporne na różne struktury obiektów Player.
        """
        if not self.squad:
            return

        def get_player_ovr(p: Any) -> int:
            if hasattr(p, "ovr"):
                return int(p.ovr)
            if isinstance(p, dict):
                return int(p.get("ovr", 50))
            return 50

        best_players = sorted(self.squad, key=get_player_ovr, reverse=True)[:top_n]
        if not best_players:
            return

        avg_ovr = sum(get_player_ovr(p) for p in best_players) / len(best_players)
        self.strength = int(round(max(1, min(100, avg_ovr))))

    def reset_season_stats(self) -> None:
        """Zeruje statystyki tabelowe przed nowym sezonem."""
        self.played = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def goal_difference(self) -> int:
        """Różnica bramek."""
        return self.goals_for - self.goals_against

    @property
    def points(self) -> int:
        """Liczba punktów w lidze."""
        return self.wins * 3 + self.draws

    def register_result(self, goals_for: int, goals_against: int) -> None:
        """Aktualizuje bilans klubu po rozegranym meczu."""
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against

        if goals_for > goals_against:
            self.wins += 1
        elif goals_for == goals_against:
            self.draws += 1
        else:
            self.losses += 1

    def to_dict(self) -> dict[str, Any]:
        """Konwertuje obiekt klubu do formatu słownika (gotowe pod API Flask)."""
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "strength": self.strength,
            "transfer_budget": self.transfer_budget,
            "colors": self.colors,
            "played": self.played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goal_difference": self.goal_difference,
            "points": self.points,
            "squad_size": len(self.squad),
        }

    def __repr__(self) -> str:
        return f"<Club {self.name} ({self.country}), OVR={self.strength}, Kadra={len(self.squad)}>"
