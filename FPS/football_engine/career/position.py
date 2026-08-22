"""
Pozycje zawodnika (punkt 5 Game Planu: 12 pozycji zamiast czterech ogólnych).
"""

from __future__ import annotations

from enum import Enum


class Position(str, Enum):
    GK = "GK"
    CB = "CB"
    LB = "LB"
    RB = "RB"
    CDM = "CDM"
    CM = "CM"
    CAM = "CAM"
    LM = "LM"
    RM = "RM"
    LW = "LW"
    RW = "RW"
    ST = "ST"


# Grupa pozycji — używana tam, gdzie nie potrzeba rozróżniać każdej z 12
# pozycji z osobna (np. ogólne komunikaty, przyszła logika składu/formacji).
class PositionGroup(str, Enum):
    GOALKEEPER = "GOALKEEPER"
    DEFENDER = "DEFENDER"
    MIDFIELDER = "MIDFIELDER"
    ATTACKER = "ATTACKER"


POSITION_GROUP: dict[Position, PositionGroup] = {
    Position.GK: PositionGroup.GOALKEEPER,
    Position.CB: PositionGroup.DEFENDER,
    Position.LB: PositionGroup.DEFENDER,
    Position.RB: PositionGroup.DEFENDER,
    Position.CDM: PositionGroup.MIDFIELDER,
    Position.CM: PositionGroup.MIDFIELDER,
    Position.CAM: PositionGroup.MIDFIELDER,
    Position.LM: PositionGroup.MIDFIELDER,
    Position.RM: PositionGroup.MIDFIELDER,
    Position.LW: PositionGroup.ATTACKER,
    Position.RW: PositionGroup.ATTACKER,
    Position.ST: PositionGroup.ATTACKER,
}
