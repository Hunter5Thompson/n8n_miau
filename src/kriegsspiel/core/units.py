from dataclasses import dataclass
from kriegsspiel.core.types import UnitType, Position

@dataclass
class Unit:
    id: str
    type: UnitType
    position: Position
    strength: float  # 0.0 - 1.0
    morale: float
    supply: float
    commander: str  # Agent ID
    
    def is_combat_effective(self) -> bool:
        return self.strength > 0.3 and self.morale > 0.4
    
    def apply_attrition(self, amount: float):
        self.strength = max(0.0, self.strength - amount)
        self.morale -= amount * 0.5