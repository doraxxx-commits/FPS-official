"""
Manager (trener) — punkty 14 i 59 Game Planu.

Kluczowa mechanika: relacja zaufania trener-zawodnik jest NIEZALEŻNA od OVR.
"Możesz mieć OVR 72, ale relację z trenerem 28, i nadal siedzieć na ławce."
Dlatego Manager przechowuje osobny słownik zaufania per zawodnik, a nie
tylko preferuje najwyższe OVR.

Różni trenerzy inaczej oceniają tego samego zawodnika (punkt 59) dzięki
`ManagerPreference` — young/experience/balanced dają różny bonus w
selection_score (squad.py) dla tego samego profilu wiekowego zawodnika.
"""

from __future__ import annotations

import uuid

from football_engine.career.player import Player

_MIN_TRUST = 0
_MAX_TRUST = 100
_DEFAULT_TRUST = 50


class ManagerPreference:
    YOUTH = "YOUTH"                # preferuje młodych zawodników
    EXPERIENCE = "EXPERIENCE"      # preferuje doświadczonych
    HIGH_OVR = "HIGH_OVR"          # gra zawsze najsilniejszym składem
    BALANCED = "BALANCED"          # brak wyraźnej preferencji wiekowej


class Manager:
    """Trener klubu — decyduje (razem z squad.py) o składzie na mecz."""

    def __init__(self, name: str, preference: str = ManagerPreference.BALANCED) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.preference = preference
        self._trust: dict[str, int] = {}

    def get_trust(self, player_id: str) -> int:
        return self._trust.get(player_id, _DEFAULT_TRUST)

    def adjust_trust(self, player_id: str, delta: int) -> int:
        """Zmienia zaufanie do zawodnika, zwraca nową wartość."""
        new_value = max(_MIN_TRUST, min(_MAX_TRUST, self.get_trust(player_id) + delta))
        self._trust[player_id] = new_value
        return new_value

    def update_trust_after_match_rating(self, player_id: str, rating: float) -> int:
        """
        Aktualizuje zaufanie na podstawie oceny meczowej zawodnika (punkt 32).
        Dobra ocena buduje zaufanie, słaba je nadgryza — to właśnie to sprawia,
        że gracz musi "dobrze grać, żeby trener stawiał na niego" (punkt 12).
        """
        if rating >= 7.5:
            delta = 4
        elif rating >= 6.5:
            delta = 1
        elif rating >= 5.5:
            delta = -1
        else:
            delta = -4
        return self.adjust_trust(player_id, delta)

    def preference_bonus(self, player: Player) -> float:
        """Dodatkowy bonus/malus do oceny zawodnika przy wyborze składu,
        wynikający z filozofii trenera (punkt 59)."""
        if self.preference == ManagerPreference.YOUTH:
            return 6.0 if player.age <= 22 else (-3.0 if player.age >= 30 else 0.0)
        if self.preference == ManagerPreference.EXPERIENCE:
            return 6.0 if player.age >= 28 else (-3.0 if player.age <= 21 else 0.0)
        if self.preference == ManagerPreference.HIGH_OVR:
            return 0.0  # OVR już mocno waży w selection_score — brak dodatkowego bonusu
        return 0.0  # BALANCED

    def __repr__(self) -> str:
        return f"<Manager {self.name} ({self.preference})>"
