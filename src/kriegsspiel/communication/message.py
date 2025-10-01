from dataclasses import dataclass
from typing import List
from kriegsspiel.core.types import Rank

@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    turn_sent: int
    turn_received: int
    priority: int = 1  # 1=normal, 2=urgent, 3=immediate
    
    def get_delay(self, sender_rank: Rank, receiver_rank: Rank) -> int:
        """Berechnet Verzögerung basierend auf Hierarchie"""
        base_delay = 1
        
        # Up the chain = schneller
        if self._is_upward(sender_rank, receiver_rank):
            base_delay = 1
        # Down the chain = langsamer
        elif self._is_downward(sender_rank, receiver_rank):
            base_delay = 2
        # Same level = mittel
        else:
            base_delay = 2
            
        # Priority reduziert delay
        return max(0, base_delay - (self.priority - 1))
    
    def _is_upward(self, from_rank: Rank, to_rank: Rank) -> bool:
        hierarchy = [Rank.TACTICAL, Rank.OPERATIONAL, Rank.STRATEGIC]
        return hierarchy.index(from_rank) < hierarchy.index(to_rank)
    
    def _is_downward(self, from_rank: Rank, to_rank: Rank) -> bool:
        return not self._is_upward(from_rank, to_rank)

class MessageQueue:
    def __init__(self):
        self.queue: List[Message] = []
    
    def add(self, message: Message):
        self.queue.append(message)
    
    def get_deliverable(self, current_turn: int) -> List[Message]:
        """Gibt Messages zurück, die jetzt ankommen"""
        deliverable = [m for m in self.queue if m.turn_received <= current_turn]
        self.queue = [m for m in self.queue if m.turn_received > current_turn]
        return deliverable