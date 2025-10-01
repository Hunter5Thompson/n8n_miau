from typing import Dict, List
from .types import Position
from .units import Unit
from ..agents.base_agent import BaseAgent

class GameState:
    """Zentraler Spielzustand"""
    
    def __init__(self, map_size: tuple):
        self.turn = 0
        self.map_size = map_size
        
        # Terrain
        self.terrain: Dict[Position, str] = {}
        self.terrain_properties: Dict[Position, dict] = {}
        
        # Einheiten und Agenten
        self.units: Dict[str, Unit] = {}
        self.agents: Dict[str, BaseAgent] = {}
        
        # Spielstatus
        self.victory_conditions = []
        self.friction_settings = {}
        self.weather = "clear"
        self.time_of_day = "0600"
        
        # Event Log
        self.event_log: List[str] = []
        
        # Side tracking
        self.blue_agents = set()
        self.red_agents = set()
    
    def add_unit(self, unit: Unit):
        self.units[unit.id] = unit
    
    def add_agent(self, agent: BaseAgent):
        self.agents[agent.id] = agent
    
    def log_event(self, event: str):
        self.event_log.append(f"T{self.turn}: {event}")
    
    def is_finished(self) -> bool:
        """Ist Spiel vorbei?"""
        return self.check_victory() or self.turn > 48
    
    def check_victory(self) -> bool:
        """Siegbedingungen prüfen"""
        for condition in self.victory_conditions:
            if condition['type'] == 'territorial':
                target = Position(
                    condition['target']['x'],
                    condition['target']['y']
                )
                # Hat eine Seite das Ziel?
                for unit in self.units.values():
                    if unit.position == target:
                        return True
        
        return False
    
    def get_friendly_agents(self, agent_id: str) -> List[str]:
        """Alle befreundeten Agenten"""
        if agent_id in self.blue_agents:
            return list(self.blue_agents)
        elif agent_id in self.red_agents:
            return list(self.red_agents)
        return []
    
    @classmethod
    def from_scenario(cls, scenario_data: dict):
        """Erstelle GameState aus Szenario-Daten"""
        # Wird vom ScenarioLoader befüllt
        return scenario_data