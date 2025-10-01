from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from kriegsspiel.core.types import Position, UnitType

@dataclass
class Observation:
    enemy_positions: List[Tuple[Position, UnitType, float]]  # Pos, Type, Confidence
    friendly_positions: List[Tuple[Position, str]]  # Position, Unit ID
    terrain_visible: Dict[Position, str]
    timestamp: int
    source: str  # "visual", "report", "recon"

@dataclass
class BeliefState:
    observations: List[Observation] = field(default_factory=list)
    enemy_strength_estimate: Dict[Position, float] = field(default_factory=dict)
    last_update: int = 0
    overall_confidence: float = 0.5
    
    def update(self, observation: Observation):
        self.observations.append(observation)
        self._decay_old_information()
        self._update_estimates()
        
    def _decay_old_information(self):
        """Information veraltet mit Zeit"""
        current_time = max(o.timestamp for o in self.observations) if self.observations else 0
        
        for obs in self.observations:
            age = current_time - obs.timestamp
            # Confidence sinkt 10% pro Turn
            decay_factor = max(0.1, 1.0 - (age * 0.1))
            # Wende decay auf alle Positionen an
            obs.enemy_positions = [
                (pos, unit_type, conf * decay_factor)
                for pos, unit_type, conf in obs.enemy_positions
            ]
    
    def _update_estimates(self):
        """Aggregiert Beobachtungen zu Schätzungen"""
        self.enemy_strength_estimate.clear()
        
        for obs in self.observations:
            for pos, _, confidence in obs.enemy_positions:
                if pos in self.enemy_strength_estimate:
                    # Kombiniere mehrere Beobachtungen
                    self.enemy_strength_estimate[pos] = max(
                        self.enemy_strength_estimate[pos],
                        confidence
                    )
                else:
                    self.enemy_strength_estimate[pos] = confidence