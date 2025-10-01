from abc import ABC, abstractmethod
from typing import List, Dict
from ..core.types import Rank, Decision
from .personality import Personality
from .belief_state import BeliefState

class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        rank: Rank,
        personality: Personality
    ):
        self.id = agent_id
        self.name = name
        self.rank = rank
        self.personality = personality
        self.belief_state = BeliefState()
        self.communication_budget = self._get_initial_comm_budget()
        self.current_orders = ""
        self.units_under_command: List[str] = []
        self.superior: str = None  # Agent ID
        self.subordinates: List[str] = []
        
    def _get_initial_comm_budget(self) -> int:
        return {
            Rank.STRATEGIC: 5,
            Rank.OPERATIONAL: 3,
            Rank.TACTICAL: 2
        }[self.rank]
    
    @abstractmethod
    def decide(self, game_state) -> Decision:
        """Jeder Agent hat eigene Decision-Logik"""
        pass
    
    @abstractmethod
    def process_orders(self, orders: str) -> None:
        """Verarbeitet Befehle von oben"""
        pass
    
    def can_communicate(self) -> bool:
        return self.communication_budget > 0
    
    def send_message(self, recipient: str, content: str) -> bool:
        if self.can_communicate():
            self.communication_budget -= 1
            return True
        return False