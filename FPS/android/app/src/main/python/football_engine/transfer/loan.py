"""
Wypożyczenia (punkt 22 Game Planu).

"Dla młodego zawodnika wypożyczenie może być świetnym ruchem." — zawodnik
tymczasowo zmienia klub, ale `original_club` jest zapamiętywany, żeby dało
się go zwrócić po zakończeniu wypożyczenia (ewentualnie z opcją wykupu).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_engine.career.player import Player
    from football_engine.world.club import Club


@dataclass
class Loan:
    player: "Player"
    original_club: "Club"
    host_club: "Club"
    duration_weeks: int
    with_buy_option: bool
    buy_option_amount: int | None = None
    weeks_remaining: int = 0
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.weeks_remaining == 0:
            self.weeks_remaining = self.duration_weeks

    def advance_week(self) -> None:
        self.weeks_remaining = max(0, self.weeks_remaining - 1)

    @property
    def is_finished(self) -> bool:
        return self.weeks_remaining <= 0


def create_loan(
    original_club: "Club",
    host_club: "Club",
    player: "Player",
    duration_weeks: int,
    with_buy_option: bool = False,
    buy_option_amount: int | None = None,
) -> Loan:
    """Przenosi zawodnika tymczasowo do klubu goszczącego i zwraca umowę wypożyczenia."""
    moved = original_club.remove_player(player.id)
    if moved is None:
        raise ValueError(f"{player.full_name} nie jest w składzie {original_club.name}")

    host_club.add_player(moved)

    return Loan(
        player=moved,
        original_club=original_club,
        host_club=host_club,
        duration_weeks=duration_weeks,
        with_buy_option=with_buy_option,
        buy_option_amount=buy_option_amount,
    )


def end_loan(loan: Loan) -> None:
    """Kończy wypożyczenie i zwraca zawodnika do klubu macierzystego."""
    moved = loan.host_club.remove_player(loan.player.id)
    if moved is None:
        raise ValueError(
            f"{loan.player.full_name} nie jest już w składzie {loan.host_club.name} "
            f"(być może wykupiony w międzyczasie?)"
        )
    loan.original_club.add_player(moved)
    loan.weeks_remaining = 0


def exercise_buy_option(loan: Loan) -> None:
    """Klub goszczący wykupuje zawodnika na stałe — kończy wypożyczenie bez zwrotu."""
    if not loan.with_buy_option:
        raise ValueError("Ta umowa wypożyczenia nie ma opcji wykupu")
    loan.original_club.transfer_budget += loan.buy_option_amount or 0
    loan.host_club.transfer_budget -= loan.buy_option_amount or 0
    loan.weeks_remaining = 0
