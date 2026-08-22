"""
Oferty i negocjacje transferowe (punkt 17 Game Planu).

Przykład z planu:
  Klub: "Oferujemy 20 000 PLN." Ty: "Chcę 28 000." Klub: "25 000 + bonusy."
  Ty: "Zgoda." Albo: Negocjacje zerwane.

Ten sam wzorzec (oferta -> ewentualna kontrpropozycja -> akceptacja/zerwanie)
stosujemy tu do opłaty transferowej między dwoma klubami — sprzedający
porównuje ofertę do szacowanej wartości zawodnika (valuation.py), kupujący
sprawdza kontrpropozycję względem swojego budżetu.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from football_engine.career.player import Player
from football_engine.transfer.valuation import estimate_market_value

if TYPE_CHECKING:
    from football_engine.world.club import Club

_ACCEPT_RATIO = 0.90     # oferta >= 90% wyceny -> sprzedający akceptuje od razu
_REJECT_RATIO = 0.55     # oferta < 55% wyceny -> sprzedający odrzuca bez rozmów
_COUNTER_RATIO = 0.95    # kontrpropozycja sprzedającego to ~95% wyceny
_MAX_ROUNDS = 3


class OfferStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass
class TransferOffer:
    buying_club: "Club"
    selling_club: "Club"
    player: Player
    final_amount: int
    status: OfferStatus
    log: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def negotiate_transfer(
    buying_club: "Club",
    selling_club: "Club",
    player: Player,
    opening_offer: int,
    buyer_max_budget: int | None = None,
) -> TransferOffer:
    """
    Prowadzi negocjacje transferowe krok po kroku (do `_MAX_ROUNDS` rund)
    między klubem kupującym a sprzedającym, w stylu dialogu z punktu 17.
    """
    valuation = estimate_market_value(player)
    buyer_max = buyer_max_budget if buyer_max_budget is not None else buying_club.transfer_budget

    log: list[str] = []
    current_offer = opening_offer

    for _ in range(_MAX_ROUNDS):
        log.append(f"{buying_club.name}: oferujemy {current_offer:,.0f}")

        if current_offer >= valuation * _ACCEPT_RATIO:
            log.append(f"{selling_club.name}: zgoda.")
            return TransferOffer(buying_club, selling_club, player, current_offer,
                                  OfferStatus.ACCEPTED, log)

        if current_offer < valuation * _REJECT_RATIO:
            log.append(f"{selling_club.name}: oferta zdecydowanie za niska, odrzucamy.")
            return TransferOffer(buying_club, selling_club, player, current_offer,
                                  OfferStatus.REJECTED, log)

        counter = round(valuation * _COUNTER_RATIO)
        log.append(f"{selling_club.name}: kontrpropozycja {counter:,.0f}")

        if counter > buyer_max:
            log.append(f"{buying_club.name}: nie stać nas na tę kwotę, wycofujemy się.")
            return TransferOffer(buying_club, selling_club, player, current_offer,
                                  OfferStatus.REJECTED, log)

        current_offer = counter

    log.append("Negocjacje przeciągają się bez porozumienia — transfer nie dochodzi do skutku.")
    return TransferOffer(buying_club, selling_club, player, current_offer,
                          OfferStatus.REJECTED, log)


def execute_transfer(offer: TransferOffer) -> None:
    """Wykonuje zaakceptowany transfer: przenosi zawodnika i rozlicza budżety."""
    if offer.status != OfferStatus.ACCEPTED:
        raise ValueError("Nie można wykonać transferu, który nie został zaakceptowany")

    moved = offer.selling_club.remove_player(offer.player.id)
    if moved is None:
        raise ValueError(f"{offer.player.full_name} nie jest już w składzie {offer.selling_club.name}")

    offer.buying_club.add_player(moved)
    offer.buying_club.transfer_budget -= offer.final_amount
    offer.selling_club.transfer_budget += offer.final_amount


def generate_career_offers(player: Player, clubs: list["Club"]) -> list[dict]:
    """
    Generuje oferty kontraktowe skierowane bezpośrednio do gracza na koniec sezonu
    lub na start kariery.
    """
    offers = []
    player_ovr = player.ovr

    for club in clubs:
        # Omiń obecny klub zawodnika
        if hasattr(player, 'club') and player.club == club:
            continue

        club_strength = getattr(club, 'strength', 60)

        # Generuj ofertę, jeśli poziom klubu pasuje do OVR gracza (tolerancja +/- 8 OVR)
        if abs(club_strength - player_ovr) <= 8:
            base_wage = max(1500, int((player_ovr ** 2) * 1.8))
            club_id = getattr(club, 'id', club.name)
            league_name = getattr(club, 'league_name', 'Liga')

            offers.append({
                "clubId": club_id,
                "club": club.name,
                "league": league_name,
                "wage": base_wage,
                "patience": 100
            })

    # Zwróć 3-4 najbardziej dopasowane oferty
    return offers[:4]
