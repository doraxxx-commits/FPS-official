"""
Symulacja meczu — Etap 2 (Rozbudowany silnik meczowy z udziałem gracza, logami i perkami).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from football_engine.world.club import Club


@dataclass(frozen=True)
class MatchResult:
    home: Club
    away: Club
    home_goals: int
    away_goals: int
    match_log: List[str] = field(default_factory=list)
    player_goals: int = 0
    player_assists: int = 0

    @property
    def winner(self) -> Club | None:
        if self.home_goals > self.away_goals:
            return self.home
        if self.away_goals > self.home_goals:
            return self.away
        return None

    def __repr__(self) -> str:
        return f"{self.home.name} {self.home_goals}-{self.away_goals} {self.away.name}"


_BASE_EXPECTED_GOALS = 1.3
_HOME_ADVANTAGE = 0.25
_STRENGTH_SCALING = 0.035


def _expected_goals(attacker: Club, defender: Club, is_home: bool) -> float:
    strength_diff = attacker.strength - defender.strength
    expected = _BASE_EXPECTED_GOALS + strength_diff * _STRENGTH_SCALING
    if is_home:
        expected += _HOME_ADVANTAGE
    return max(0.15, expected)


def _poisson_sample(lam: float, rng: random.Random) -> int:
    """Implementacja losowania z rozkładu Poissona (algorytm Knutha)."""
    l_threshold = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= l_threshold:
            return k - 1


def simulate_match(
    home: Club, 
    away: Club, 
    player: Optional[Any] = None, 
    is_player_home: bool = True, 
    rng: Optional[random.Random] = None
) -> MatchResult:
    """
    Symuluje mecz między klubami na bazie rozkładu Poissona z uwzględnieniem
    akcji gracza, aktywnych perków oraz generowaniem logu meczowego.
    """
    rng = rng or random.Random()

    home_lambda = _expected_goals(home, away, is_home=True)
    away_lambda = _expected_goals(away, home, is_home=False)

    base_home_goals = _poisson_sample(home_lambda, rng)
    base_away_goals = _poisson_sample(away_lambda, rng)

    match_log: List[str] = []
    player_goals = 0
    player_assists = 0

    # Rozgrywka akcja-po-akcji z udziałem gracza
    if player is not None:
        unlocked_perk_ids = [
            p.id if hasattr(p, "id") else p.get("id")
            for p in getattr(player, "perks", [])
            if (p.unlocked if hasattr(p, "unlocked") else p.get("unlocked", False))
        ]

        clutch_bonus = 1.25 if "clutch" in unlocked_perk_ids else 1.0

        for minute in range(10, 91, 15):
            chance = rng.random() * clutch_bonus

            if chance > 0.72:
                # Szansa na bramkę gracza
                if "free_kick" in unlocked_perk_ids and rng.random() > 0.45:
                    match_log.append(f"{minute}' 🎯 [Specjalista Wolnych] Niesamowity strzał z rzutu wolnego prosto w okienko!")
                    player_goals += 1
                elif rng.random() > 0.55:
                    match_log.append(f"{minute}' ⚽ GOAL! Doskonałe wykończenie akcji w pole karne!")
                    player_goals += 1
                else:
                    match_log.append(f"{minute}' 🧤 Mocny strzał na bramkę, ale bramkarz popisuje się świetną paradą.")

            elif chance > 0.50:
                # Szansa na asystę gracza
                if rng.random() > 0.55:
                    match_log.append(f"{minute}' 🅰️ Znakomite otwierające podanie i partner zamienia sytuację na gola!")
                    player_assists += 1
                else:
                    match_log.append(f"{minute}' 👟 Dobre rozegranie w środku pola i podanie na skrzydło.")

        if not match_log:
            match_log.append("90' Zacięty mecz, walka toczyła się głównie w środku pola.")

    # Sumowanie wyniku z uwzględnieniem bramek gracza
    if is_player_home:
        final_home_goals = base_home_goals + player_goals
        final_away_goals = base_away_goals
    else:
        final_home_goals = base_home_goals
        final_away_goals = base_away_goals + player_goals

    return MatchResult(
        home=home,
        away=away,
        home_goals=final_home_goals,
        away_goals=final_away_goals,
        match_log=match_log,
        player_goals=player_goals,
        player_assists=player_assists
    )
