from enum import Enum
from dataclasses import dataclass
from typing import Optional

class Terrain(Enum):
    OPEN = "open"
    FOREST = "forest"
    HILL = "hill"
    RIVER = "river"
    ROAD = "road"
    TOWN = "town"

class UnitType(Enum):
    INFANTRY = "infantry"
    ARMOR = "armor"
    RECON = "recon"
    ARTILLERY = "artillery"

class Rank(Enum):
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    TACTICAL = "tactical"

class Action(Enum):
    MOVE = "move"
    ATTACK = "attack"
    DEFEND = "defend"
    RECON = "recon"
    REPORT = "report"
    WAIT = "wait"
    REQUEST_SUPPORT = "request_support"

@dataclass
class Position:
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

@dataclass
class Decision:
    agent_id: str
    action: Action
    target: Optional[Position]
    reasoning: str
    confidence: float