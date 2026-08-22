"""
Demo Etapu 7: reprezentacja — powołania, skład na mecz, EURO (grupy + puchar).

Uruchomienie: python demo_national.py
"""

import random

from football_engine.career.attributes import Attributes
from football_engine.career.player import Player
from football_engine.career.position import Position
from football_engine.club.squad import select_matchday_squad
from football_engine.match.simulation import simulate_match
from football_engine.national.callup import call_up_squad
from football_engine.national.national_team import NationalTeam, NationalTeamTier
from football_engine.national.tournament import InternationalTournament

rng = random.Random(5)


def make_national_pool(country: str, base_strength: int, n: int = 30) -> list[Player]:
    """Generuje pulę zawodników danego kraju o różnym wieku (do powołań U19-SENIOR)."""
    players = []
    positions = list(Position)
    for i in range(n):
        position = positions[i % len(positions)]
        age = 17 + (i % 18)  # rozrzut wiekowy 17-34
        base = max(40, min(90, base_strength + rng.randint(-12, 12)))
        gk_base = base if position == Position.GK else 1
        attrs = Attributes(
            pace=base, acceleration=base, dribbling=base, ball_control=base,
            passing=base, vision=base, technique=base, positioning=base,
            strength=base, stamina=base, finishing=base, shot_power=base, heading=base,
            tackling=base, marking=base,
            reflexes=gk_base, handling=gk_base, diving=gk_base, kicking=gk_base,
        )
        players.append(Player(f"Zawodnik{i}", country, age, country, position, attrs,
                               potential=min(99, base + 10)))
    return players


# --- Punkt 38: powołanie do kadry U21 (nie musi czekać na "kolejkę" wieku) ---
polska_pool = make_national_pool("Polska", base_strength=65)
u21_squad = call_up_squad(NationalTeamTier.U21, "Polska", polska_pool)

polska_u21 = NationalTeam("Polska", NationalTeamTier.U21)
polska_u21.squad = u21_squad

print(f"Powołani do {polska_u21.name}: {len(polska_u21.squad)} zawodników, "
      f"siła kadry = {polska_u21.strength}")
print(f"Najstarszy powołany: {max(p.age for p in polska_u21.squad)} lat "
      f"(limit dla U21: 21)\n")

# --- Reużycie club/squad.py: wybór składu na mecz reprezentacji ---
selection = select_matchday_squad(polska_u21)
print("=== SKŁAD NA MECZ (reużyty silnik wyboru składu z Etapu 3) ===")
for p in selection.starting_xi:
    print(f"  {p.position.value:<4} {p.full_name} (OVR {p.ovr})")

# --- Mecz towarzyski Polska U21 vs Niemcy U21 ---
niemcy_pool = make_national_pool("Niemcy", base_strength=72)
niemcy_u21 = NationalTeam("Niemcy", NationalTeamTier.U21)
niemcy_u21.squad = call_up_squad(NationalTeamTier.U21, "Niemcy", niemcy_pool)

print(f"\n=== MECZ TOWARZYSKI ===")
result = simulate_match(polska_u21, niemcy_u21, rng=rng)
print(f"  {result}")

# --- Mini-EURO: 2 grupy po 4 drużyny, top 2 z grupy do fazy pucharowej ---
print(f"\n=== MINI-EURO: FAZA GRUPOWA + PUCHAROWA ===\n")

countries = [
    ("Polska", 65), ("Niemcy", 72), ("Francja", 74), ("Hiszpania", 73),
    ("Włochy", 70), ("Anglia", 71), ("Portugalia", 69), ("Holandia", 68),
]
teams = []
for country, strength in countries:
    pool = make_national_pool(country, base_strength=strength)
    team = NationalTeam(country, NationalTeamTier.SENIOR)
    team.squad = call_up_squad(NationalTeamTier.SENIOR, country, pool)
    teams.append(team)

group_a = teams[:4]
group_b = teams[4:]

euro = InternationalTournament("EURO", groups=[group_a, group_b],
                                teams_advancing_per_group=2, rng=rng)
group_tables = euro.play_group_stage()

for group_index, standings in group_tables.items():
    label = "A" if group_index == 0 else "B"
    print(f"--- Grupa {label} ---")
    for pos, team in enumerate(standings, start=1):
        print(f"  {pos}. {team.name:<12} M:{team.played} PKT:{team.points} "
              f"+/-:{team.goal_difference:+d}")
    print()

champion = euro.play_knockout_stage()
print(f"🏆 MISTRZ MINI-EURO: {champion.name}")

if champion.country == "Polska":
    print("🇵🇱 Polska mistrzem Europy! Historyczny sukces reprezentacji.")
