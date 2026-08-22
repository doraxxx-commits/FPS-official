"""
Demo Etapu 5: świat — wiele lig, awanse/spadki, ewolucja siły klubów.

Uruchomienie: python demo_world.py
"""

import random

from football_engine.season.standings import print_table
from football_engine.time_engine import GameCalendar
from football_engine.world.club import Club
from football_engine.world.league import League
from football_engine.world.league_system import LeagueSystem
from football_engine.world.world_engine import WorldEngine

rng = random.Random(11)

# --- Ekstraklasa (tier 0) ---
ekstraklasa = League("Ekstraklasa", "Polska", [
    Club("Legia Warszawa", "Polska", strength=78),
    Club("Lech Poznań", "Polska", strength=76),
    Club("Raków Częstochowa", "Polska", strength=74),
    Club("Jagiellonia Białystok", "Polska", strength=70),
    Club("Pogoń Szczecin", "Polska", strength=68),
    Club("Cracovia", "Polska", strength=60),  # najsłabsza — kandydat do spadku
])

# --- 1 Liga (tier 1) ---
pierwsza_liga = League("1 Liga", "Polska", [
    Club("GKS Katowice", "Polska", strength=64),
    Club("Widzew Łódź", "Polska", strength=62),  # najlepsza — kandydat do awansu
    Club("Chrobry Głogów", "Polska", strength=55),
    Club("Stal Mielec", "Polska", strength=53),
    Club("Odra Opole", "Polska", strength=50),
    Club("Górnik Łęczna", "Polska", strength=48),
])

system = LeagueSystem(
    country="Polska",
    leagues=[ekstraklasa, pierwsza_liga],
    promotion_count=1,
    relegation_count=1,
)
print(system)

calendar = GameCalendar(start_season="2026/27")
world = WorldEngine(system, calendar, rng=rng)

print(f"\n=== TABELE PRZED SEZONEM {calendar.season} ===")
print_table(ekstraklasa)
print_table(pierwsza_liga)

news = world.simulate_full_season()

print(f"\n=== KONIEC SEZONU — NOWY SEZON: {calendar.season} ===")
print("\n📰 NEWS — AWANSE I SPADKI:")
for line in news:
    print(f"  {line}")

print(f"\nSkład Ekstraklasy po zmianach: {[c.name for c in ekstraklasa.clubs]}")
print(f"Skład 1 Ligi po zmianach: {[c.name for c in pierwsza_liga.clubs]}")

# --- Drugi sezon, żeby pokazać, że system dalej żyje ---
print(f"\n=== SYMULUJEMY KOLEJNY SEZON ({calendar.season}) ===")
news_2 = world.simulate_full_season()
print(f"Nowy sezon: {calendar.season}")
for line in news_2:
    print(f"  {line}")

print(f"\nEkstraklasa po 2 sezonach: {[c.name for c in ekstraklasa.clubs]}")
