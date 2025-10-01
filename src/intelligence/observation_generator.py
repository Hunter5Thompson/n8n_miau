from typing import List, Tuple
from ..agents.belief_state import Observation
from ..core.types import Position, UnitType
from ..agents.base_agent import BaseAgent
from ..core.game_state import GameState
import random

class ObservationGenerator:
    """Generiert Beobachtungen für Agenten - Fog of War"""
    
    def generate_observation(
        self,
        agent: BaseAgent,
        game_state: GameState,
        visibility_range: int
    ) -> Observation:
        """Generiert Observation für Agent"""
        
        # Sammle sichtbare feindliche Einheiten
        enemy_positions = []
        
        for unit in game_state.units.values():
            if self._is_enemy(unit, agent, game_state):
                distance = self._get_distance_to_agent_units(unit, agent, game_state)
                
                if distance <= visibility_range:
                    confidence = self._calculate_confidence(distance, visibility_range)
                    
                    # Füge Unsicherheit hinzu
                    confidence *= random.uniform(0.7, 1.0)
                    
                    enemy_positions.append((
                        unit.position,
                        unit.type,
                        confidence
                    ))
        
        # Sammle eigene Einheiten (immer sichtbar)
        friendly_positions = [
            (game_state.units[uid].position, uid)
            for uid in agent.units_under_command
        ]
        
        # Sichtbares Terrain
        terrain_visible = self._get_visible_terrain(
            agent, game_state, visibility_range
        )
        
        return Observation(
            enemy_positions=enemy_positions,
            friendly_positions=friendly_positions,
            terrain_visible=terrain_visible,
            timestamp=game_state.turn,
            source="visual"
        )
    
    def generate_recon_observation(
        self,
        position: Position,
        game_state: GameState,
        quality: float
    ) -> Observation:
        """Dedizierte Aufklärung - bessere Qualität"""
        
        enemy_positions = []
        
        for unit in game_state.units.values():
            distance = unit.position.distance_to(position)
            
            if distance <= 3:  # Recon range
                confidence = quality * (1.0 - distance / 4.0)
                
                enemy_positions.append((
                    unit.position,
                    unit.type,
                    confidence
                ))
        
        return Observation(
            enemy_positions=enemy_positions,
            friendly_positions=[],
            terrain_visible={},
            timestamp=game_state.turn,
            source="recon"
        )
    
    def _is_enemy(self, unit, agent: BaseAgent, game_state: GameState) -> bool:
        """Ist Einheit feindlich?"""
        return unit.commander not in game_state.get_friendly_agents(agent.id)
    
    def _get_distance_to_agent_units(
        self,
        enemy_unit,
        agent: BaseAgent,
        game_state: GameState
    ) -> int:
        """Minimale Distanz zu einer eigenen Einheit"""
        if not agent.units_under_command:
            return 999
        
        distances = [
            enemy_unit.position.distance_to(game_state.units[uid].position)
            for uid in agent.units_under_command
        ]
        
        return min(distances)
    
    def _calculate_confidence(self, distance: int, max_range: int) -> float:
        """Confidence sinkt mit Distanz"""
        return max(0.3, 1.0 - (distance / max_range))
    
    def _get_visible_terrain(
        self,
        agent: BaseAgent,
        game_state: GameState,
        visibility_range: int
    ) -> dict:
        """Sichtbares Terrain"""
        visible = {}
        
        # Von allen eigenen Einheiten aus
        for uid in agent.units_under_command:
            unit = game_state.units[uid]
            
            for pos, terrain in game_state.terrain.items():
                if pos.distance_to(unit.position) <= visibility_range:
                    visible[pos] = terrain
        
        return visible