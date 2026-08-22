"""
Demo Etapu 3: klub — skład, trener, rywalizacja o pierwszy skład.

Uruchomienie: python demo_club.py
"""

from football_engine.career.attributes import Attributes
from football_engine.career.player import Player
from football_engine.career.position import Position
from football_engine.club.manager import Manager, ManagerPreference
from football_engine.club.squad import describe_position_battle, select_matchday_squad
from football_engine.world.club import Club


def make_player(name: str, age: int, ovr_bias: int, position: Position) -> Player:
    """Pomocnicze: tworzy zawodnika z atrybutami przesuniętymi o ovr_bias
    względem wartości bazowej 55, żeby łatwo zbudować rywalizującą kadrę."""
    base = 55 + ovr_bias
    gk_base = base if position == Position.GK else 1
    attrs = Attributes(
        pace=base, acceleration=base, dribbling=base, ball_control=base,
        passing=base, vision=base, technique=base, positioning=base,
        strength=base, stamina=base, finishing=base, shot_power=base, heading=base,
        tackling=base, marking=base,
        reflexes=gk_base, handling=gk_base, diving=gk_base, kicking=gk_base,
    )
    first, last = name.split(" ", 1)
    return Player(first, last, age, "Polska", position, attrs, potential=min(99, base + 15))


club = Club("Legia Warszawa", "Polska", strength=75)
manager = Manager("Kosta Runjaić", preference=ManagerPreference.BALANCED)
club.set_manager(manager)

# Punkt 12 Game Planu: przykładowa rywalizacja napastników.
st1 = make_player("Marek Kowalski", age=27, ovr_bias=23, position=Position.ST)   # ~78 OVR
st2 = make_player("Jakub Nowak", age=24, ovr_bias=19, position=Position.ST)      # ~74 OVR
ty = make_player("Mateusz Kowalski", age=19, ovr_bias=14, position=Position.ST)  # ~69 OVR, TY = "Ty"
st4 = make_player("Piotr Zieliński", age=30, ovr_bias=7, position=Position.ST)   # ~62 OVR

for p in (st1, st2, ty, st4):
    club.add_player(p)

# Reszta minimalnego składu, żeby dało się wybrać pełne 11 (uproszczone: po
# jednym zawodniku na pozostałe wymagane pozycje formacji).
for position in [Position.GK, Position.CB, Position.CB, Position.LB, Position.RB,
                  Position.CDM, Position.CM, Position.CAM, Position.LW, Position.RW]:
    club.add_player(make_player(f"Zawodnik {position.value}", age=25, ovr_bias=10, position=position))

club.recalculate_strength_from_squad()
print(f"{club.name}: siła przeliczona ze składu = {club.strength}\n")

print("=== RYWALIZACJA O POZYCJĘ ST ===")
for p in sorted((st1, st2, ty, st4), key=lambda x: x.ovr, reverse=True):
    print(f"  {p.full_name:<20} OVR {p.ovr}, forma {p.form}, zaufanie trenera "
          f"{manager.get_trust(p.id)}")
print(f"\n{describe_position_battle(club, Position.ST)}")

print("\n=== SKŁAD NA MECZ (przed zmianą formy/zaufania) ===")
selection = select_matchday_squad(club)
print("Podstawowa jedenastka:")
for p in selection.starting_xi:
    print(f"  {p.position.value:<4} {p.full_name} (OVR {p.ovr})")

# --- Ty (młody napastnik) rozgrywasz świetną serię meczów, budując zaufanie ---
print("\n--- Ty rozgrywasz 3 mecze na 8.0+, trener zaczyna Ci ufać ---")
for _ in range(3):
    manager.update_trust_after_match_rating(ty.id, rating=8.2)
    ty.apply_form_change(+6)

# --- Marek Kowalski (dotychczasowy lider) łapie serię słabych występów ---
print("--- Marek Kowalski notuje serię słabych występów ---")
for _ in range(3):
    manager.update_trust_after_match_rating(st1.id, rating=5.0)
    st1.apply_form_change(-6)

print(f"\n{describe_position_battle(club, Position.ST)}")

print("\n=== SKŁAD NA MECZ (po zmianie formy/zaufania) ===")
selection = select_matchday_squad(club)
st_starter = [p for p in selection.starting_xi if p.position == Position.ST][0]
print(f"Napastnik w podstawowym składzie: {st_starter.full_name}")

if st_starter.id == ty.id:
    print("🟢 Trener stawia teraz na Ciebie.")
elif st_starter.id == st1.id:
    print("Marek Kowalski nadal utrzymuje miejsce w składzie.")
