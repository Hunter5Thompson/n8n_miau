from typing import Optional, List
import random
from dataclasses import dataclass

@dataclass
class FrictionEvent:
    type: str
    description: str
    effects: dict
    duration: int  # Turns

class FrictionGenerator:
    def __init__(self, base_probability: float = 0.2):
        self.base_probability = base_probability
        self.active_events: List[FrictionEvent] = []
        
    def generate(self, game_state) -> Optional[FrictionEvent]:
        """Generiert Friction basierend auf Spielsituation"""
        
        # Erhöhe Wahrscheinlichkeit bei intensivem Kampf
        current_prob = self._calculate_probability(game_state)
        
        if random.random() < current_prob:
            return self._create_event(game_state)
        return None
    
    def _calculate_probability(self, game_state) -> float:
        prob = self.base_probability
        
        # Modifikatoren
        if game_state.turn > 10:
            prob += 0.1  # Längere Kämpfe = mehr Friction
        
        # Mehr Einheiten = mehr Chaos
        unit_count = len(game_state.units)
        if unit_count > 10:
            prob += 0.05
            
        return min(0.5, prob)  # Max 50%
    
    def _create_event(self, game_state) -> FrictionEvent:
        events = [
            self._weather_event,
            self._communication_breakdown,
            self._supply_issue,
            self._civilian_interference,
            self._false_intelligence
        ]
        
        return random.choice(events)(game_state)
    
    def _weather_event(self, game_state) -> FrictionEvent:
        return FrictionEvent(
            type="weather",
            description="Heavy rain reduces visibility and mobility",
            effects={
                "movement_modifier": 0.7,
                "recon_range": -2,
                "artillery_effectiveness": 0.6
            },
            duration=random.randint(2, 4)
        )
    
    def _communication_breakdown(self, game_state) -> FrictionEvent:
        return FrictionEvent(
            type="communication",
            description="Radio equipment failure in sector",
            effects={
                "communication_delay": +2,
                "coordination_penalty": 0.5
            },
            duration=random.randint(1, 3)
        )
    
    def _supply_issue(self, game_state) -> FrictionEvent:
        return FrictionEvent(
            type="logistics",
            description="Supply convoy delayed at river crossing",
            effects={
                "supply_rate": 0.5,
                "unit_effectiveness": 0.8
            },
            duration=random.randint(2, 3)
        )
    
    def _civilian_interference(self, game_state) -> FrictionEvent:
        return FrictionEvent(
            type="civilian",
            description="Refugee column blocks main supply route",
            effects={
                "road_movement": 0.3,
                "time_delay": +1
            },
            duration=random.randint(1, 2)
        )
    
    def _false_intelligence(self, game_state) -> FrictionEvent:
        return FrictionEvent(
            type="intelligence",
            description="Conflicting reports on enemy strength",
            effects={
                "belief_confidence": -0.3,
                "decision_uncertainty": +0.2
            },
            duration=1
        )