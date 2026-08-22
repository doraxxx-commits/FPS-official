"""
Okna transferowe (punkt 18 Game Planu).

🟢 LETNIE OKNO: 1 lipca – 31 sierpnia
🔵 ZIMOWE OKNO: 1 stycznia – 31 stycznia

Poza tymi zakresami transfery są zamknięte (poza wyjątkami typu wolny
agent — punkt 23 — które dojdą razem z pełną obsługą kontraktów).
"""

from __future__ import annotations

import datetime
from enum import Enum

from football_engine.time_engine import GameCalendar


class TransferWindow(str, Enum):
    SUMMER = "SUMMER"
    WINTER = "WINTER"


def get_active_window(current_date: datetime.date) -> TransferWindow | None:
    """Zwraca aktywne okno transferowe dla podanej daty, albo None jeśli zamknięte."""
    if current_date.month == 1:
        return TransferWindow.WINTER
    if current_date.month in (7, 8):
        return TransferWindow.SUMMER
    return None


def is_window_open(calendar: GameCalendar) -> bool:
    return get_active_window(calendar.current_date) is not None


def describe_window_status(calendar: GameCalendar) -> str:
    window = get_active_window(calendar.current_date)
    if window == TransferWindow.SUMMER:
        return "🟢 LETNIE OKNO TRANSFEROWE OTWARTE"
    if window == TransferWindow.WINTER:
        return "🔵 ZIMOWE OKNO TRANSFEROWE OTWARTE"
    return "🔒 TRANSFERY ZAMKNIĘTE"
