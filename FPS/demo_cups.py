"""
Demo Etapu 6: puchary — Puchar Polski (jednomecz, redraw co rundę) +
kwalifikacja i rozgrywki europejskie (dwumecz).

Uruchomienie: python demo_cups.py
"""

import random

from football_engine.cup.cup_engine import CupEngine
from football_engine.cup.qualification import EuropeanAllocation, get_european_qualifiers
from football_engine.season.standings import build_table, print_table
from football_engine.season.season_engine import SeasonEngine
from football_engine.world.club import Club
from football_engine.world.league import League

rng = random.Random(21)

names = [
    "Legia Warszawa", "Lech Poznań", "Raków Częstochowa", "Jagiellonia Białystok",
    "Pogoń Szczecin", "Górnik Zabrze", "Widzew Łódź", "Cracovia",
    "Piast Gliwice", "Zagłębie Lubin", "Radomiak Radom", "Korona Kielce",
    "Puszcza Niepołomice", "Motor Lublin", "Warta Poznań", "Śląsk Wrocław",
]
strengths = [78, 76, 74, 70, 68, 60, 58, 62, 55, 57, 52, 54, 50, 51, 53, 65]
clubs = [Club(n, "Polska", s) for n, s in zip(names, strengths)]

print("=== PUCHAR POLSKI: 16 klubów, jednomeczowe rundy, losowanie co rundę ===\n")
cup = CupEngine("Puchar Polski", clubs, two_legged=False, rng=rng)

while not cup.is_finished:
    results = cup.play_next_round()
    round_name = results[0].tie.round_name
    print(f"--- {round_name} ---")
    for r in results:
        if r.decided_by_bye:
            print(f"  {r.winner.name} — WOLNY LOS, awans bez gry")
        else:
            leg = r.legs[0]
            tiebreak = " (po dogrywce/karnych)" if r.decided_by_tiebreak else ""
            print(f"  {leg}{tiebreak} -> awansuje {r.winner.name}")
    print()

print(f"🏆 ZWYCIĘZCA PUCHARU POLSKI: {cup.champion.name}\n")

# --- Kwalifikacja europejska na podstawie tabeli ligowej ---
print("=== KWALIFIKACJA EUROPEJSKA (na podstawie tabeli Ekstraklasy) ===\n")
league = League("Ekstraklasa", "Polska", clubs[:8])  # top-8 jako przykładowa ekstraklasa
season = SeasonEngine(league, rng=rng)
season.simulate_remaining_season()
print_table(league)

qualifiers = get_european_qualifiers(season.get_table(), EuropeanAllocation(
    champions_league_spots=1, europa_league_spots=1, conference_league_spots=2,
))
print("\n📰 KWALIFIKACJA:")
for competition, teams in qualifiers.items():
    for team in teams:
        print(f"  {team.name} -> {competition}")

# --- Liga Konferencji: dwumeczowe rundy pucharowe ---
print("\n=== PRZYKŁADOWA LIGA KONFERENCJI (dwumecz) ===\n")
conference_pool = qualifiers["Liga Konferencji"] + [
    Club("Slovan Bratysława", "Słowacja", 66),
    Club("Fola Esch", "Luksemburg", 45),
]
euro_cup = CupEngine("Liga Konferencji", conference_pool, two_legged=True, rng=rng)

while not euro_cup.is_finished:
    results = euro_cup.play_next_round()
    round_name = results[0].tie.round_name
    print(f"--- {round_name} ---")
    for r in results:
        if r.decided_by_bye:
            print(f"  {r.winner.name} — WOLNY LOS")
        else:
            leg1, leg2 = r.legs
            tiebreak = " (dogrywka/karne po dwumeczu)" if r.decided_by_tiebreak else ""
            print(f"  {leg1} | rewanż: {leg2}{tiebreak} -> awansuje {r.winner.name}")
    print()

print(f"🏆 ZWYCIĘZCA LIGI KONFERENCJI: {euro_cup.champion.name}")
