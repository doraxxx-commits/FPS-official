"""
Rozwój zawodnika (punkty 7-8 Game Planu).

Model wzrostu na sezon:
- młodzież (<=23 lat): szybki wzrost, tym szybszy im większa "przestrzeń"
  do potencjału (potential - obecne OVR), modyfikowany rozegranymi minutami.
- wiek szczytowy (24-29 lat): wzrost wypłaszcza się, może się jeszcze
  nieznacznie poprawiać przy dużej liczbie minut.
- schyłek (30+): stopniowy spadek, przyspieszający po 33. roku życia.

Przyrost/spadek OVR jest następnie rozłożony na atrybuty istotne dla
pozycji zawodnika (te z największą wagą w POSITION_WEIGHTS rosną/maleją
najbardziej) — dzięki temu rozwój jest spójny z tym, jak liczone jest OVR.
"""

from __future__ import annotations

from dataclasses import fields

from football_engine.career.attributes import POSITION_WEIGHTS
from football_engine.career.player import Player

_MIN_ATTR = 1
_MAX_ATTR = 99


def _growth_points(player: Player, minutes_played_season: int) -> int:
    """Wylicza, o ile punktów OVR ma się zmienić zawodnik w tym sezonie."""
    potential_gap = max(0, player.potential - player.ovr)
    # Współczynnik rozegranych minut: 0.0 (brak gry) do 1.0 (pełny sezon, ~3000 min).
    minutes_factor = min(1.0, minutes_played_season / 3000)

    if player.age <= 23:
        base = 2 + potential_gap * 0.25
        return round(base * (0.4 + 0.6 * minutes_factor))
    elif player.age <= 29:
        base = 0.5 + potential_gap * 0.1
        return round(base * (0.4 + 0.6 * minutes_factor))
    else:
        decline_base = -1 if player.age <= 33 else -3
        # Zawodnicy z dużą liczbą minut nawet w schyłkowym wieku tracą wolniej.
        return round(decline_base * (1.2 - 0.4 * minutes_factor))


def apply_season_development(player: Player, minutes_played_season: int) -> int:
    """
    Aktualizuje atrybuty zawodnika na koniec sezonu i zwiększa jego wiek o 1.

    Args:
        player: zawodnik do rozwinięcia.
        minutes_played_season: suma minut rozegranych w sezonie — więcej
            minut przyspiesza rozwój (i spowalnia spadek formy w schyłku kariery).

    Returns:
        Faktyczna zmiana OVR w tym sezonie (dodatnia lub ujemna).
    """
    ovr_before = player.ovr
    delta = _growth_points(player, minutes_played_season)

    weights = POSITION_WEIGHTS[player.position]
    max_weight = max(weights.values())
    # Rozkładamy deltę OVR na atrybuty proporcjonalnie do ich wagi na tej
    # pozycji: atrybut najważniejszy dla pozycji (max_weight) rośnie/maleje
    # o pełną deltę, pozostałe waż­one atrybuty proporcjonalnie mniej — dzięki
    # temu np. finishing napastnika rośnie wyraźnie szybciej niż jego tackling.
    # Atrybuty spoza wag danej pozycji zmieniają się śladowo, żeby zawodnik
    # nie stawał się jednowymiarowy.
    for f in fields(player.attributes):
        attr_name = f.name
        weight = weights.get(attr_name, 0.0)
        if weight > 0:
            attr_delta = delta * (weight / max_weight)
        else:
            attr_delta = delta * (0.15 / len(fields(player.attributes)))
        current = getattr(player.attributes, attr_name)
        new_value = round(current + attr_delta)
        setattr(player.attributes, attr_name, max(_MIN_ATTR, min(_MAX_ATTR, new_value)))

    player.attributes.clamp()
    player.age += 1

    return player.ovr - ovr_before
