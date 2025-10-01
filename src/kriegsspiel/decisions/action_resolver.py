from typing import List, Dict, Optional
from kriegsspiel.core.types import Decision, Position, Action, UnitType
from kriegsspiel.core.game_state import GameState

class ActionResolver:
    """Maps abstract Decisions to unit-level atomic actions and validates feasibility."""

    def resolve(self, decision: Decision, game_state: GameState) -> List[Dict]:
        """
        Returns a list of atomic actions based on a high-level decision.
        For now, only handles MOVE actions.
        """
        actions: List[Dict] = []

        if decision.action == Action.MOVE:
            actions = self._resolve_move(decision, game_state)

        # Future actions like ATTACK, RECON will be handled here.
        # elif decision.action == Action.ATTACK:
        #     actions = self._resolve_attack(decision, game_state)

        return actions

    def _resolve_move(self, decision: Decision, game_state: GameState) -> List[Dict]:
        """Resolves a MOVE decision into a list of atomic move actions."""
        resolved_actions: List[Dict] = []
        try:
            agent = game_state.agents[decision.agent_id]
            destination = decision.target
        except KeyError:
            print(f"ERROR: Agent {decision.agent_id} not found in game state.")
            return []

        if not destination:
            print(f"ERROR: MOVE decision for agent {agent.id} is missing a target.")
            return []

        for unit_id in agent.units_under_command:
            unit = game_state.units.get(unit_id)
            if not unit:
                print(f"WARNING: Unit {unit_id} for agent {agent.id} not found in game state.")
                continue

            max_move_points = self._get_unit_movement_range(unit.type)
            distance = unit.position.distance_to(destination)

            # Simple validation: checks cost of destination tile only, not path.
            terrain_props = game_state.terrain_properties.get(destination, {})
            movement_cost = terrain_props.get('movement_cost', 1.0)

            total_cost = distance * movement_cost

            if total_cost <= max_move_points:
                resolved_actions.append({
                    "type": "move",
                    "unit_id": unit.id,
                    "to": destination,
                })
            else:
                # Per design: "Validierungsfehler sauber loggen, nicht crashen."
                print(f"Validation failed for {unit.id}: Move to {destination} with cost {total_cost:.2f} exceeds max range {max_move_points}.")

        return resolved_actions

    def _get_unit_movement_range(self, unit_type: UnitType) -> int:
        """Returns the base movement range from the design document."""
        if unit_type == UnitType.INFANTRY:
            return 2
        if unit_type == UnitType.ARMOR:
            return 4
        if unit_type == UnitType.RECON:
            return 6
        return 1 # Default for other types like ARTILLERY