"""
Demo Etapu 1: czas + sezony + mecze + tabela.

Uruchomienie: python demo.py
"""

import random

from football_engine.season.season_engine import SeasonEngine
from football_engine.season.standings import print_table
from football_engine.time_engine import GameCalendar
from football_engine.world.club import Club
from football_engine.world.league import League

rng = random.Random(42)  # deterministyczne demo

clubs = [
    Club("Legia Warszawa", "Polska", strength=78),
    Club("Lech Poznań", "Polska", strength=76),
    Club("Raków Częstochowa", "Polska", strength=74),
    Club("Pogoń Szczecin", "Polska", strength=68),
    Club("Jagiellonia Białystok", "Polska", strength=70),
    Club("Górnik Zabrze", "Polska", strength=60),
    Club("Widzew Łódź", "Polska", strength=58),
    Club("Cracovia", "Polska", strength=62),
]

league = League(name="Ekstraklasa", country="Polska", clubs=clubs)
calendar = GameCalendar(start_season="2026/27")
season = SeasonEngine(league, rng=rng)

print(f"Start sezonu {calendar.season} — {season.total_matchdays} kolejek, {len(clubs)} klubów\n")

# --- Rozgrywamy pierwszą kolejkę osobno (przykład Trybu 1: pierwszy mecz) ---
first_matchday_results = season.simulate_matchday()
calendar.advance_matchday()
print(f"Kolejka {calendar.matchday - 1}:")
for result in first_matchday_results:
    print(f"  {result}")

# --- Reszta sezonu symulowana na raz (przykład Trybu 3: symuluj sezon) ---
season.simulate_remaining_season()
calendar.matchday = season.total_matchdays

print_table(league)

print(f"\nSezon {calendar.season} zakończony po {season.total_matchdays} kolejkach.")
print(f"Rozegranych meczów łącznie: {len(season.results)}")
