from typing import Dict, List
from kriegsspiel.core.types import Position
from kriegsspiel.core.units import Unit
from kriegsspiel.agents.base_agent import BaseAgent

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
        from kriegsspiel.core.types import Rank, UnitType
        from kriegsspiel.agents.strategic_agent import StrategicAgent
        from kriegsspiel.agents.operational_agent import OperationalAgent
        from kriegsspiel.agents.tactical_agent import TacticalAgent
        from kriegsspiel.agents.personality import PersonalityLoader

        map_cfg = scenario_data.get('map', {})
        size = map_cfg.get('size', {'x': 0, 'y': 0})
        game_state = cls(map_size=(size.get('x', 0), size.get('y', 0)))

        # Grundzustände
        scenario_cfg = scenario_data.get('scenario', {})
        game_state.victory_conditions = scenario_cfg.get('victory_conditions', [])
        game_state.friction_settings = scenario_data.get('friction_settings', {})

        initial_conditions = scenario_data.get('initial_conditions', {})
        game_state.weather = initial_conditions.get('weather', game_state.weather)
        game_state.time_of_day = initial_conditions.get('time_of_day', game_state.time_of_day)

        # Terrain laden (inkl. Eigenschaften)
        for terrain_entry in map_cfg.get('terrain', []):
            pos_cfg = terrain_entry.get('pos', {})
            pos = Position(x=pos_cfg.get('x', 0), y=pos_cfg.get('y', 0))
            terrain_type = terrain_entry.get('type', 'open')

            game_state.terrain[pos] = terrain_type

            props = {k: v for k, v in terrain_entry.items() if k != 'pos'}
            props.setdefault('type', terrain_type)
            props.setdefault('cover', 0.0)
            props.setdefault('movement_cost', 1.0 if terrain_type != 'river' else 999.0)
            game_state.terrain_properties[pos] = props

        personality_cache = PersonalityLoader.load_profiles()
        default_personality = personality_cache.get('balanced', PersonalityLoader.get_profile('balanced'))

        def _create_agent(agent_data: dict, rank: Rank):
            personality_name = agent_data.get('personality', 'balanced')
            personality = personality_cache.get(
                personality_name, default_personality
            )

            if rank == Rank.STRATEGIC:
                return StrategicAgent(
                    agent_id=agent_data['id'],
                    name=agent_data['name'],
                    personality=personality,
                )
            if rank == Rank.OPERATIONAL:
                return OperationalAgent(
                    agent_id=agent_data['id'],
                    name=agent_data['name'],
                    personality=personality,
                )
            return TacticalAgent(
                agent_id=agent_data['id'],
                name=agent_data['name'],
                personality=personality,
            )

        forces_cfg = scenario_data.get('forces', {})

        for side, side_cfg in forces_cfg.items():
            side_agents = game_state.blue_agents if side == 'blue' else game_state.red_agents
            command_structure = side_cfg.get('command_structure', {})
            agents_by_id: Dict[str, BaseAgent] = {}

            for level, rank in (
                ('strategic', Rank.STRATEGIC),
                ('operational', Rank.OPERATIONAL),
                ('tactical', Rank.TACTICAL),
            ):
                for agent_data in command_structure.get(level, []):
                    agent = _create_agent(agent_data, rank)
                    game_state.add_agent(agent)
                    agents_by_id[agent.id] = agent
                    side_agents.add(agent.id)

            # Beziehungen herstellen
            for level in ('strategic', 'operational', 'tactical'):
                for agent_data in command_structure.get(level, []):
                    agent = agents_by_id.get(agent_data['id'])
                    if not agent:
                        continue
                    if 'superior' in agent_data:
                        agent.superior = agent_data['superior']
                        superior = agents_by_id.get(agent.superior)
                        if superior and agent.id not in superior.subordinates:
                            superior.subordinates.append(agent.id)

            # Einheiten laden
            for unit_data in side_cfg.get('units', []):
                unit = Unit(
                    id=unit_data['id'],
                    type=UnitType[unit_data['type'].upper()],
                    position=Position(
                        x=unit_data['position']['x'],
                        y=unit_data['position']['y'],
                    ),
                    strength=unit_data['strength'],
                    morale=unit_data['morale'],
                    supply=unit_data['supply'],
                    commander=unit_data['commander'],
                )

                equipment = unit_data.get('equipment', {})
                if equipment:
                    unit.equipment_quality = equipment.get('quality', 0.8)
                    unit.primary_weapon = equipment.get('primary_weapon')
                    if 'ammunition' in equipment:
                        unit.ammunition = equipment['ammunition']
                        unit.ammunition_quality = equipment.get('ammunition_quality', 1.0)
                else:
                    unit.equipment_quality = 0.8
                    unit.ammunition_quality = 1.0

                game_state.add_unit(unit)

                commander = agents_by_id.get(unit.commander)
                if commander and unit.id not in commander.units_under_command:
                    commander.units_under_command.append(unit.id)

        return game_state
