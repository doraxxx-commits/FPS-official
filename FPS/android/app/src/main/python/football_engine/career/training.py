"""
Trening (punkt 9 Game Planu): kategorie treningu mają wpływać na KONKRETNE
atrybuty, a nie tylko dorzucać punkty do samego OVR.

To są małe, cotygodniowe przyrosty (w przeciwieństwie do dużego skoku
sezonowego z development.py) — regularny trening buduje zawodnika
stopniowo, sezon jedynie "zbiera" ten postęp poprzez potencjał i minuty.
"""

from __future__ import annotations

from enum import Enum

from football_engine.career.player import Player

_MAX_ATTR = 99
_MIN_ATTR = 1


class TrainingFocus(str, Enum):
    TECHNIQUE = "TECHNIQUE"        # technika, drybling, podania
    PHYSICAL = "PHYSICAL"          # szybkość, stamina, siła
    SHOOTING = "SHOOTING"          # finishing, shot_power
    TACTICAL = "TACTICAL"          # positioning, vision
    RECOVERY = "RECOVERY"          # kondycja, forma


_TRAINING_ATTRIBUTES: dict[TrainingFocus, list[str]] = {
    TrainingFocus.TECHNIQUE: ["technique", "dribbling", "passing"],
    TrainingFocus.PHYSICAL: ["pace", "stamina", "strength"],
    TrainingFocus.SHOOTING: ["finishing", "shot_power"],
    TrainingFocus.TACTICAL: ["positioning", "vision"],
    TrainingFocus.RECOVERY: [],  # RECOVERY nie rusza atrybutów, tylko kondycję/formę
}

# Ile punktu zyskuje każdy trenowany atrybut za sesję (bardzo mały, cotygodniowy przyrost).
_ATTRIBUTE_GAIN_PER_SESSION = 0.3
# Koszt kondycji za sesję treningową (poza regeneracją).
_CONDITION_COST = 8


def train(player: Player, focus: TrainingFocus | str) -> None:
    """
    Przeprowadza jedną sesję treningową w wybranej kategorii.

    RECOVERY podnosi kondycję i formę zamiast je obciążać — to świadomy
    wybór gracza "odpuszczam trening techniczny, żeby nie ryzykować kontuzji"
    (patrz punkt 10: ostrzeżenie o rosnącym ryzyku kontuzji przy niskiej kondycji).
    """
    if player.is_injured:
        raise RuntimeError(f"{player.full_name} jest kontuzjowany i nie może trenować")

    # Zabezpieczenie: konwersja ze ciągu znaków (str) na Enum TrainingFocus
    if isinstance(focus, str):
        try:
            focus = TrainingFocus(focus.upper())
        except ValueError:
            # Domyślny bezpieczny trening w razie przekazania nieznanego klucza z frontendu
            focus = TrainingFocus.TECHNIQUE

    if focus == TrainingFocus.RECOVERY:
        player.rest(days=2)
        player.apply_form_change(+3)
        return

    for attr_name in _TRAINING_ATTRIBUTES[focus]:
        if hasattr(player.attributes, attr_name):
            current = getattr(player.attributes, attr_name)
            new_value = round(current + _ATTRIBUTE_GAIN_PER_SESSION)
            setattr(player.attributes, attr_name, max(_MIN_ATTR, min(_MAX_ATTR, new_value)))

    if hasattr(player.attributes, 'clamp'):
        player.attributes.clamp()

    player.condition = max(0, player.condition - _CONDITION_COST)
    
    # Przeliczenie OVR po zakończonym treningu
    if hasattr(player, 'recalculate_ovr'):
        player.recalculate_ovr()
