"""
Demo Etapu 2: zawodnik — OVR, atrybuty, potencjał, forma, kondycja, kontuzje.

Uruchomienie: python demo_player.py
"""

import random

from football_engine.career.attributes import Attributes
from football_engine.career.development import apply_season_development
from football_engine.career.injury import check_for_injury
from football_engine.career.player import Player
from football_engine.career.position import Position
from football_engine.career.training import TrainingFocus, train

rng = random.Random(7)

# 17-letni napastnik, przykład z punktu 63 Game Planu ("Start: 17 lat, 52 OVR").
player = Player(
    first_name="Mateusz",
    last_name="Kowalski",
    age=17,
    country="Polska",
    position=Position.ST,
    attributes=Attributes(
        pace=68, acceleration=66, dribbling=58, ball_control=56,
        passing=48, vision=45, technique=54, positioning=55,
        strength=52, stamina=60, finishing=57, shot_power=53, heading=50,
        tackling=30, marking=28,
    ),
    potential=86,  # wysoki potencjał — "może stać się gwiazdą" (punkt 7)
)

print(player)
print(f"OVR startowe: {player.ovr}\n")

# --- Symulujemy sezon: 20 tygodni treningu + 15 rozegranych meczów ---
minutes_played_season = 0

for week in range(1, 21):
    if player.is_injured:
        player.advance_week()
        continue

    # Prosty rozkład: co drugi tydzień mecz, w pozostałych trening.
    if week % 2 == 0:
        minutes = 90
        player.play_match(minutes)
        minutes_played_season += minutes

        injury = check_for_injury(player.condition, rng=rng)
        if injury:
            player.set_injury(injury)
            print(f"[Tydzień {week}] 🏥 Kontuzja: {injury.name} ({injury.total_weeks} tyg.)")
        else:
            # Losowy wpływ formy po meczu (punkt 33).
            form_change = rng.choice([-8, -3, 2, 5, 9])
            player.apply_form_change(form_change)
    else:
        focus = rng.choice(list(TrainingFocus))
        train(player, focus)

    player.rest(days=2)  # naturalna regeneracja między sesjami

print(f"\nPo 20 tygodniach: kondycja={player.condition}, forma={player.form}, "
      f"minuty w sezonie={minutes_played_season}")
print(f"OVR po treningach w sezonie: {player.ovr}")

# --- Rozwój na koniec sezonu (punkt 8) ---
delta = apply_season_development(player, minutes_played_season)
print(f"\n=== KONIEC SEZONU ===")
print(f"Zmiana OVR: {delta:+d}")
print(player)
