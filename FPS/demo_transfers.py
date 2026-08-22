"""
Demo Etapu 4: transfery — okna, AI klubów, negocjacje, wypożyczenia.

Uruchomienie: python demo_transfers.py
"""

import datetime
import random

from football_engine.career.attributes import Attributes
from football_engine.career.player import Player
from football_engine.career.position import Position
from football_engine.time_engine import GameCalendar
from football_engine.transfer.ai import run_transfer_window
from football_engine.transfer.loan import create_loan, end_loan
from football_engine.transfer.offer import negotiate_transfer, execute_transfer, OfferStatus
from football_engine.transfer.valuation import estimate_market_value
from football_engine.transfer.window import describe_window_status
from football_engine.world.club import Club

rng = random.Random(3)


def make_player(name: str, age: int, ovr_bias: int, position: Position) -> Player:
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
    return Player(first, last, age, "Polska", position, attrs, potential=min(99, base + 10))


def build_minimal_squad(club: Club, star_position: Position, star_age: int, star_bias: int) -> Player:
    """Buduje minimalny skład klubu z jednym 'gwiazdorskim' zawodnikiem na
    star_position (często starzejącym się, żeby wywołać potrzebę transferu)."""
    star = make_player(f"Gwiazda {club.name}", star_age, star_bias, star_position)
    club.add_player(star)
    for position in Position:
        if position == star_position:
            continue
        club.add_player(make_player(f"Zawodnik {club.name} {position.value}", 25, 5, position))
    return star


# --- Budujemy 3 kluby: jeden z potrzebą transferową, dwa potencjalne źródła ---
legia = Club("Legia Warszawa", "Polska", strength=75, transfer_budget=15_000_000)
lech = Club("Lech Poznań", "Polska", strength=74, transfer_budget=8_000_000)
rakow = Club("Raków Częstochowa", "Polska", strength=70, transfer_budget=6_000_000)

# Legia ma 33-letniego napastnika — punkt 21: "Mam 33-letniego napastnika,
# potrzebuję młodego następcy."
aging_striker = build_minimal_squad(legia, Position.ST, star_age=33, star_bias=15)
young_target = build_minimal_squad(lech, Position.ST, star_age=21, star_bias=13)
build_minimal_squad(rakow, Position.CB, star_age=27, star_bias=8)

calendar = GameCalendar(start_season="2026/27", start_date=datetime.date(2026, 7, 5))
print(describe_window_status(calendar))
print(f"Data: {calendar.current_date.isoformat()}\n")

print(f"Wartość rynkowa {young_target.full_name} ({young_target.ovr} OVR, "
      f"{young_target.age} lat): {estimate_market_value(young_target):,.0f}")
print(f"Budżet transferowy Legii: {legia.transfer_budget:,.0f}\n")

# --- Ręczna negocjacja pojedynczego transferu ---
print("=== NEGOCJACJE: Legia -> Lech Poznań (młody napastnik) ===")
opening_offer = round(estimate_market_value(young_target) * 0.7)
offer = negotiate_transfer(legia, lech, young_target, opening_offer)
for line in offer.log:
    print(f"  {line}")

if offer.status == OfferStatus.ACCEPTED:
    execute_transfer(offer)
    print(f"✅ Transfer zakończony: {young_target.full_name} -> {legia.name} "
          f"za {offer.final_amount:,.0f}\n")
else:
    print("❌ Transfer nie doszedł do skutku.\n")

# --- Runda AI: kluby same identyfikują potrzeby i próbują kupować ---
print("=== AI TRANSFEROWE (cała liga) ===")
clubs = [legia, lech, rakow]
completed = run_transfer_window(clubs, calendar, rng=rng)
if completed:
    for t in completed:
        print(f"📰 {t.buying_club.name} kupuje {t.player.full_name} od "
              f"{t.selling_club.name} za {t.final_amount:,.0f}")
else:
    print("Brak zawartych transferów w tej rundzie AI.")

# --- Wypożyczenie: młody zawodnik Raków -> Legia na pół roku, z opcją wykupu ---
print("\n=== WYPOŻYCZENIE ===")
young_cb = make_player("Adam Wojtas", age=19, ovr_bias=3, position=Position.CB)
rakow.add_player(young_cb)
loan = create_loan(rakow, legia, young_cb, duration_weeks=26, with_buy_option=True,
                    buy_option_amount=2_000_000)
print(f"{young_cb.full_name} wypożyczony: {loan.original_club.name} -> "
      f"{loan.host_club.name} na {loan.duration_weeks} tygodni "
      f"(opcja wykupu: {loan.buy_option_amount:,.0f})")
print(f"Czy {young_cb.full_name} jest teraz w składzie Legii? "
      f"{'tak' if young_cb.id in [p.id for p in legia.squad] else 'nie'}")

end_loan(loan)
print(f"Po zakończeniu wypożyczenia — z powrotem w składzie {rakow.name}? "
      f"{'tak' if young_cb.id in [p.id for p in rakow.squad] else 'nie'}")

# --- Poza oknem transferowym ---
print("\n=== POZA OKNEM TRANSFEROWYM ===")
calendar.advance_days(60)  # przeskakujemy do września
print(describe_window_status(calendar))
blocked = run_transfer_window(clubs, calendar, rng=rng)
print(f"Transfery zawarte poza oknem: {len(blocked)} (musi być 0)")
