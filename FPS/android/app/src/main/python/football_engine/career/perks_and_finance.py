from dataclasses import dataclass
from enum import Enum
from typing import List

class PerkType(str, Enum):
    FREE_KICK_SPECIALIST = "Specjalista Wolnych"
    IRON_LUNGS = "Żelazne Płuca"
    DRESSING_ROOM_LEADER = "Lider Szatni"
    CLUTCH_PLAYER = "Gracz Kluczowych Momentów"

@dataclass
class Perk:
    id: str
    name: str
    description: str
    cost_skill_points: int
    unlocked: bool = False

DEFAULT_PERKS = [
    Perk("free_kick", "Specjalista Wolnych", "Zwiększa szansę na gola z rzutów wolnych i strzałów z dystansu.", 2),
    Perk("iron_lungs", "Żelazne Płuca", "Spowolniony spadek kondycji w trakcie meczu i szybsza regeneracja.", 3),
    Perk("leader", "Lider Szatni", "Zwiększa zaufanie trenera i morale zespołu.", 2),
    Perk("clutch", "Gracz Kluczowych Momentów", "Wyższa skuteczność w końcówkach meczów i ważnych pucharach.", 4),
]

class FinancialEngine:
    def __init__(self):
        self.balance: int = 5000
        self.weekly_salary: int = 1500
        self.personal_trainer: bool = False
        self.agent_tier: int = 1  # 1: Amator, 2: Profesjonalista, 3: Światowy Agent

    def receive_salary(self):
        self.balance += self.weekly_salary

    def hire_trainer(self) -> bool:
        if self.balance >= 10000 and not self.personal_trainer:
            self.balance -= 10000
            self.personal_trainer = True
            return True
        return False

    def upgrade_agent(self) -> bool:
        cost = self.agent_tier * 25000
        if self.balance >= cost and self.agent_tier < 3:
            self.balance -= cost
            self.agent_tier += 1
            return True
        return False

class PlayerRelationship:
    def __init__(self):
        self.manager_trust: int = 50  # 0 - 100
        self.fan_approval: int = 50   # 0 - 100

    def modify_trust(self, amount: int):
        self.manager_trust = max(0, min(100, self.manager_trust + amount))

    def modify_approval(self, amount: int):
        self.fan_approval = max(0, min(100, self.fan_approval + amount))
