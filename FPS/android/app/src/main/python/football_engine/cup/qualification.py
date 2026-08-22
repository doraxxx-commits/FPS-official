"""
Kwalifikacja do pucharów europejskich (punkty 26, 37 Game Planu).

Punkt 26: "Kolorowanie: 🟢 Liga mistrzów / europejskie puchary". Miejsca w
tabeli ligowej przekładają się bezpośrednio na miejsca w europejskich
pucharach — najlepsi trafiają do Ligi Mistrzów, kolejni do Ligi Europy,
kolejni do Ligi Konferencji.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from football_engine.season.standings import StandingsRow
    from football_engine.world.club import Club


@dataclass
class EuropeanAllocation:
    champions_league_spots: int = 1
    europa_league_spots: int = 1
    conference_league_spots: int = 2


def get_european_qualifiers(
    table: list["StandingsRow"], allocation: EuropeanAllocation | None = None
) -> dict[str, list["Club"]]:
    """
    Zwraca kluby zakwalifikowane do każdego z pucharów europejskich na
    podstawie końcowej tabeli ligowej, w kolejności: Liga Mistrzów -> Liga
    Europy -> Liga Konferencji (kolejne miejsca w tabeli, bez nakładania się).
    """
    allocation = allocation or EuropeanAllocation()
    sorted_clubs = [row.club for row in table]

    cl_end = allocation.champions_league_spots
    el_end = cl_end + allocation.europa_league_spots
    ecl_end = el_end + allocation.conference_league_spots

    return {
        "Liga Mistrzów": sorted_clubs[:cl_end],
        "Liga Europy": sorted_clubs[cl_end:el_end],
        "Liga Konferencji": sorted_clubs[el_end:ecl_end],
    }
