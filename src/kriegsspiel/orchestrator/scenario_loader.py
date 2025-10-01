import yaml
from pathlib import Path
from typing import Dict
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import Position, Terrain
from kriegsspiel.core.units import Unit, UnitType
from kriegsspiel.agents.strategic_agent import StrategicAgent
from kriegsspiel.agents.operational_agent import OperationalAgent
from kriegsspiel.agents.tactical_agent import TacticalAgent
from kriegsspiel.agents.personality import PersonalityLoader

class ScenarioLoader:
    """Lädt Szenarien aus YAML"""
    
    @staticmethod
    def load(scenario_path: str) -> GameState:
        """Lädt komplettes Szenario"""
        
        with open(scenario_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Erstelle Game State
        map_size = data['map']['size']
        game_state = GameState(
            map_size=(map_size['x'], map_size['y'])
        )
        
        # Lade Terrain
        ScenarioLoader._load_terrain(game_state, data['map'])
        
        # Lade Agenten und Einheiten
        ScenarioLoader._load_forces(game_state, data['forces'])
        
        # Lade Siegbedingungen
        game_state.victory_conditions = data['scenario']['victory_conditions']
        
        # Lade Friction Settings
        game_state.friction_settings = data.get('friction_settings', {})
        
        # Initial Conditions
        game_state.weather = data['initial_conditions']['weather']
        game_state.time_of_day = data['initial_conditions']['time_of_day']
        
        return game_state
    
    @staticmethod
    def _load_terrain(game_state: GameState, map_data: Dict):
        """Lädt Terrain"""
        for terrain_entry in map_data['terrain']:
            pos = Position(
                x=terrain_entry['pos']['x'],
                y=terrain_entry['pos']['y']
            )
            terrain_type = terrain_entry['type']

            game_state.terrain[pos] = terrain_type

            props = {k: v for k, v in terrain_entry.items() if k != 'pos'}
            props.setdefault('type', terrain_type)
            props.setdefault('cover', 0.0)
            props.setdefault('movement_cost', 1.0 if terrain_type != 'river' else 999.0)

            game_state.terrain_properties[pos] = props
    
    @staticmethod
    def _load_forces(game_state: GameState, forces_data: Dict):
        """Lädt beide Seiten"""
        for side, side_data in forces_data.items():
            ScenarioLoader._load_side(game_state, side, side_data)
    
    # src/orchestrator/scenario_loader.py
    @staticmethod
    def _load_side(game_state: GameState, side: str, side_data: Dict):
        """Lädt eine Seite (blue/red)"""
        
        # KRITISCH: Side-Set definieren
        side_set = game_state.blue_agents if side == "blue" else game_state.red_agents
        
        agent_hierarchy = side_data['command_structure']
        agents = {}
        
        # Strategic level
        for agent_data in agent_hierarchy.get('strategic', []):
            agent = ScenarioLoader._create_agent(agent_data, 'strategic')
            agents[agent.id] = agent
            game_state.add_agent(agent)
            side_set.add(agent.id)  # HINZUGEFÜGT
        
        # Operational level
        for agent_data in agent_hierarchy.get('operational', []):
            agent = ScenarioLoader._create_agent(agent_data, 'operational')
            agents[agent.id] = agent
            game_state.add_agent(agent)
            side_set.add(agent.id)  # HINZUGEFÜGT

            if 'superior' in agent_data:
                agent.superior = agent_data['superior']
                superior = agents.get(agent_data['superior'])
                if superior and agent.id not in superior.subordinates:
                    superior.subordinates.append(agent.id)

        # Tactical level
        for agent_data in agent_hierarchy.get('tactical', []):
            agent = ScenarioLoader._create_agent(agent_data, 'tactical')
            agents[agent.id] = agent
            game_state.add_agent(agent)
            side_set.add(agent.id)  # HINZUGEFÜGT

            if 'superior' in agent_data:
                agent.superior = agent_data['superior']
                superior = agents.get(agent_data['superior'])
                if superior and agent.id not in superior.subordinates:
                    superior.subordinates.append(agent.id)
        
        
        # Lade Einheiten
        for unit_data in side_data['units']:
            unit = ScenarioLoader._create_unit(unit_data)
            game_state.add_unit(unit)

            # Verknüpfe mit Commander
            commander = agents.get(unit.commander)
            if commander and unit.id not in commander.units_under_command:
                commander.units_under_command.append(unit.id)
    
    @staticmethod
    def _create_agent(agent_data: Dict, rank_str: str):
        """Erstellt Agent aus YAML-Daten"""
        from kriegsspiel.core.types import Rank
        
        rank = {
            'strategic': Rank.STRATEGIC,
            'operational': Rank.OPERATIONAL,
            'tactical': Rank.TACTICAL
        }[rank_str]
        
        # Personality
        personality_name = agent_data.get('personality', 'balanced')
        personality = PersonalityLoader.get_profile(personality_name)
        
        # Erstelle richtigen Agent-Type
        if rank == Rank.STRATEGIC:
            agent = StrategicAgent(
                agent_id=agent_data['id'],
                name=agent_data['name'],
                personality=personality
            )
        elif rank == Rank.OPERATIONAL:
            agent = OperationalAgent(
                agent_id=agent_data['id'],
                name=agent_data['name'],
                personality=personality
            )
        else:
            agent = TacticalAgent(
                agent_id=agent_data['id'],
                name=agent_data['name'],
                personality=personality
            )
        
        return agent
    
    @staticmethod
    def _create_unit(unit_data: Dict) -> Unit:
        unit = Unit(
            id=unit_data['id'],
            type=UnitType[unit_data['type'].upper()],
            position=Position(
                x=unit_data['position']['x'],
                y=unit_data['position']['y']
            ),
            strength=unit_data['strength'],
            morale=unit_data['morale'],
            supply=unit_data['supply'],
            commander=unit_data['commander']
        )

        # Equipment mit Defaults
        if 'equipment' in unit_data:
            eq = unit_data['equipment']
            unit.equipment_quality = eq.get('quality', 0.8)
            unit.primary_weapon = eq.get('primary_weapon')

            if 'ammunition' in eq:
                unit.ammunition = eq['ammunition']
                unit.ammunition_quality = 1.0
        else:
            # Fallback wenn kein Equipment definiert
            unit.equipment_quality = 0.8
            unit.ammunition_quality = 1.0

        return unit
