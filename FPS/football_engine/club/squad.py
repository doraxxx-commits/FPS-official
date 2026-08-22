"""
Skład meczowy i rywalizacja o miejsce w składzie (punkty 12-13 Game Planu).

"Nie masz automatycznie miejsca w składzie. Musisz trenować, dobrze grać,
mieć dobrą formę, zdobywać zaufanie trenera." — dlatego `selection_score`
NIE jest samym OVR: to OVR + forma + kondycja + zaufanie do trenera +
filozofia trenera (punkt 59). Dwóch zawodników o tym samym OVR może
zajmować zupełnie różne miejsce w hierarchii składu.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from football_engine.career.player import Player
from football_engine.career.position import Position
from football_engine.club.manager import Manager

if TYPE_CHECKING:
    # Tylko do podpowiedzi typów — uniknięcie importu w runtime zapobiega
    # cyklowi: world.club importuje club.manager, więc club.squad nie może
    # w runtime importować world.club z powrotem.
    from football_engine.world.club import Club

# Domyślna formacja (odpowiednik 4-3-3) — 11 miejsc w składzie podstawowym.
DEFAULT_FORMATION: dict[Position, int] = {
    Position.GK: 1,
    Position.CB: 2,
    Position.LB: 1,
    Position.RB: 1,
    Position.CDM: 1,
    Position.CM: 1,
    Position.CAM: 1,
    Position.LW: 1,
    Position.RW: 1,
    Position.ST: 1,
}

_DEFAULT_TRUST = 50
_BENCH_SIZE = 7


def selection_score(player: Player, manager: Manager | None) -> float:
    """
    Ocena zawodnika przy wyborze składu — punkt 14: OVR nie wystarcza,
    liczy się też forma, kondycja i zaufanie trenera.

    Kontuzjowany zawodnik dostaje wynik uniemożliwiający wybór do składu.
    """
    if player.is_injured:
        return float("-inf")

    trust = manager.get_trust(player.id) if manager else _DEFAULT_TRUST
    score = player.ovr * 0.55 + player.form * 0.20 + player.condition * 0.10 + trust * 0.15
    if manager:
        score += manager.preference_bonus(player)
    return score


@dataclass
class SquadSelection:
    starting_xi: list[Player]
    bench: list[Player]
    out_of_squad: list[Player]


def select_matchday_squad(
    club: Club,
    formation: dict[Position, int] | None = None,
    bench_size: int = _BENCH_SIZE,
) -> SquadSelection:
    """
    Wybiera skład na mecz: 11 zawodników w podstawowym składzie (najlepsi
    per pozycja wg `selection_score`), do `bench_size` na ławce, reszta
    poza kadrą meczową. Kontuzjowani i zawodnicy spoza wymaganych pozycji
    (gdy brakuje obsady) po prostu nie trafiają do składu podstawowego.
    """
    formation = formation or DEFAULT_FORMATION
    manager = club.manager
    available = [p for p in club.squad if not p.is_injured]

    starting_xi: list[Player] = []
    used_ids: set[str] = set()

    for position, needed in formation.items():
        candidates = sorted(
            (p for p in available if p.position == position),
            key=lambda p: selection_score(p, manager),
            reverse=True,
        )
        chosen = candidates[:needed]
        starting_xi.extend(chosen)
        used_ids.update(p.id for p in chosen)

    remaining = sorted(
        (p for p in available if p.id not in used_ids),
        key=lambda p: selection_score(p, manager),
        reverse=True,
    )
    bench = remaining[:bench_size]
    out_of_squad = remaining[bench_size:]

    return SquadSelection(starting_xi=starting_xi, bench=bench, out_of_squad=out_of_squad)


def get_position_battle(club: Club, position: Position) -> list[tuple[Player, float]]:
    """Zwraca zawodników na danej pozycji posortowanych wg `selection_score`
    malejąco, razem z ich wynikiem — do prezentacji rywalizacji (punkt 13)."""
    manager = club.manager
    contenders = club.players_at_position(position)
    scored = [(p, selection_score(p, manager)) for p in contenders]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)


def describe_position_battle(club: Club, position: Position, close_gap: float = 4.0) -> str:
    """
    Generuje krótki komunikat w stylu mediów z punktu 13
    ("W klubie trwa walka o miejsce...") na podstawie aktualnego rankingu.
    """
    battle = get_position_battle(club, position)
    if len(battle) < 2:
        if len(battle) == 1:
            return f"{battle[0][0].full_name} nie ma obecnie konkurencji na pozycji {position.value}."
        return f"Brak zawodników na pozycji {position.value} w składzie."

    leader, leader_score = battle[0]
    challenger, challenger_score = battle[1]
    gap = leader_score - challenger_score

    if gap <= close_gap:
        return (
            f"🔥 W klubie trwa walka o miejsce na pozycji {position.value}: "
            f"{leader.full_name} vs {challenger.full_name}."
        )
    return f"🟢 Trener stawia na {leader.full_name} na pozycji {position.value}."
