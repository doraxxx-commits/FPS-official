"""
AI transferowe klubów (punkty 19-21, 58 Game Planu).

"Klub nie kupuje losowego zawodnika. [...] Mam 33-letniego napastnika.
AI: Potrzebuję młodego następcy. Szukamy: 18-23 lata, ST, OVR 70-75,
budżet 30M." — dlatego `identify_club_needs` patrzy nie tylko na braki
liczbowe w składzie, ale i na wiek najlepszego zawodnika na pozycji,
a `find_transfer_target` filtruje kandydatów po wieku i budżecie,
zamiast losować dowolnego zawodnika.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from football_engine.career.position import Position
from football_engine.club.squad import DEFAULT_FORMATION
from football_engine.transfer.offer import (
    OfferStatus,
    TransferOffer,
    execute_transfer,
    negotiate_transfer,
)
from football_engine.transfer.valuation import estimate_market_value
from football_engine.transfer.window import is_window_open

if TYPE_CHECKING:
    from football_engine.career.player import Player
    from football_engine.time_engine import GameCalendar
    from football_engine.world.club import Club

_AGING_THRESHOLD = 32       # powyżej tego wieku klub szuka następcy (punkt 21)
_TARGET_MIN_AGE = 18
_TARGET_MAX_AGE = 27
_OPENING_OFFER_RATIO = 0.80  # pierwsza oferta AI to ~80% szacowanej wartości


def identify_club_needs(
    club: "Club", formation: dict[Position, int] | None = None
) -> list[Position]:
    """
    Zwraca pozycje, na których klub potrzebuje wzmocnienia: albo brakuje
    obsady (mniej niż wymagane + 1 zmiennik), albo najlepszy zawodnik na
    tej pozycji zaczyna się starzeć i potrzebny jest następca.
    """
    formation = formation or DEFAULT_FORMATION
    needs: list[Position] = []

    for position, required in formation.items():
        candidates = [p for p in club.players_at_position(position) if not p.is_injured]

        if len(candidates) < required + 1:
            needs.append(position)
            continue

        best = max(candidates, key=lambda p: p.ovr)
        if best.age >= _AGING_THRESHOLD:
            needs.append(position)

    return needs


def find_transfer_target(
    buying_club: "Club", all_clubs: list["Club"], position: Position
) -> tuple["Player", "Club", int] | None:
    """
    Szuka najlepszego dostępnego kandydata na daną pozycję wśród innych
    klubów, mieszczącego się w budżecie i preferowanym przedziale wiekowym.
    Zwraca (zawodnik, klub sprzedający, szacowana wartość) albo None.
    """
    candidates: list[tuple["Player", "Club", int]] = []

    for club in all_clubs:
        if club.id == buying_club.id:
            continue
        for player in club.players_at_position(position):
            if player.is_injured:
                continue
            if not (_TARGET_MIN_AGE <= player.age <= _TARGET_MAX_AGE):
                continue
            value = estimate_market_value(player)
            if value <= buying_club.transfer_budget:
                candidates.append((player, club, value))

    if not candidates:
        return None

    # Spośród tych, na które stać klub, wybieramy najsilniejszego (punkt 21:
    # konkretny przedział OVR/wieku, nie przypadkowy zawodnik).
    candidates.sort(key=lambda c: c[0].ovr, reverse=True)
    return candidates[0]


def run_transfer_window(
    clubs: list["Club"], calendar: "GameCalendar", rng: random.Random | None = None
) -> list[TransferOffer]:
    """
    Jedna "przebiegówka" AI transferowego: każdy klub z potrzebą próbuje
    znaleźć i kupić zawodnika. Zwraca listę zaakceptowanych transferów
    (nieudane negocjacje nie trafiają na tę listę, ale są widoczne w logu
    zwracanego TransferOffer, jeśli wywołujący chce je zebrać osobno).

    Nie robi nic poza oknem transferowym (punkt 18).
    """
    if not is_window_open(calendar):
        return []

    rng = rng or random.Random()
    completed: list[TransferOffer] = []

    # Losowa kolejność klubów, żeby żaden nie miał stałej przewagi "pierwszeństwa".
    shuffled_clubs = list(clubs)
    rng.shuffle(shuffled_clubs)

    for club in shuffled_clubs:
        needs = identify_club_needs(club)
        for position in needs:
            target = find_transfer_target(club, clubs, position)
            if target is None:
                continue

            player, selling_club, value = target
            opening_offer = round(value * _OPENING_OFFER_RATIO)
            offer = negotiate_transfer(club, selling_club, player, opening_offer)

            if offer.status == OfferStatus.ACCEPTED:
                execute_transfer(offer)
                completed.append(offer)

    return completed
