import logging
from typing import List, Dict
from kriegsspiel.core.types import Decision, Action, UnitType
from kriegsspiel.core.game_state import GameState

logger = logging.getLogger(__name__)

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
        elif decision.action == Action.ATTACK:
            actions = self._resolve_attack(decision, game_state)
        elif decision.action == Action.RECON:
            actions = self._resolve_recon(decision, game_state)
        elif decision.action == Action.REQUEST_SUPPORT:
            actions = self._resolve_support_request(decision, game_state)
        elif decision.action == Action.DEFEND:
            actions = self._resolve_defend(decision, game_state)

        # Future actions like ATTACK, RECON will be handled here.
        # elif decision.action == Action.ATTACK:
        #     actions = self._resolve_attack(decision, game_state)

        return actions

    def _resolve_move(self, decision: Decision, game_state: GameState) -> List[Dict]:
        """Resolves a MOVE decision into a list of atomic move actions."""
        resolved_actions: List[Dict] = []
        agent = game_state.agents.get(decision.agent_id)
        if not agent:
            logger.error("Agent %s not found for MOVE decision", decision.agent_id)
            return []

        destination = decision.target
        if not destination:
            logger.error("MOVE decision for %s is missing a target", agent.id)
            return []

        for unit_id in agent.units_under_command:
            unit = game_state.units.get(unit_id)
            if not unit:
                logger.warning("Unit %s for agent %s missing in game state", unit_id, agent.id)
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
                logger.info(
                    "Move validation failed for %s: distance cost %.2f exceeds max %.2f",
                    unit.id,
                    total_cost,
                    max_move_points,
                )

        return resolved_actions

    def _resolve_attack(self, decision: Decision, game_state: GameState) -> List[Dict]:
        agent = game_state.agents.get(decision.agent_id)
        if not agent:
            logger.error("Agent %s not found for ATTACK decision", decision.agent_id)
            return []

        if not decision.target:
            logger.error("ATTACK decision for %s missing target", agent.id)
            return []

        enemy_commanders = set(game_state.get_friendly_agents(agent.id))
        enemy_units = [
            unit for unit in game_state.units.values()
            if unit.position == decision.target and unit.commander not in enemy_commanders
        ]

        if not enemy_units:
            logger.info("No enemies present at %s for attack by %s", decision.target, agent.id)

        actions: List[Dict] = []
        for unit_id in agent.units_under_command:
            unit = game_state.units.get(unit_id)
            if not unit:
                logger.warning("Unit %s for agent %s missing in game state", unit_id, agent.id)
                continue

            attack_range = self._get_unit_attack_range(unit.type)
            distance = unit.position.distance_to(decision.target)

            if distance <= attack_range:
                actions.append({
                    "type": "attack",
                    "unit_id": unit.id,
                    "target": decision.target,
                    "estimated_enemy_strength": sum(u.strength for u in enemy_units),
                })
            else:
                logger.info(
                    "Attack validation failed for %s: distance %s exceeds range %s",
                    unit.id,
                    distance,
                    attack_range,
                )

        return actions

    def _resolve_recon(self, decision: Decision, game_state: GameState) -> List[Dict]:
        agent = game_state.agents.get(decision.agent_id)
        if not agent:
            logger.error("Agent %s not found for RECON decision", decision.agent_id)
            return []

        if not decision.target:
            logger.error("RECON decision for %s missing target", agent.id)
            return []

        actions: List[Dict] = []
        recon_units = []
        for unit_id in agent.units_under_command:
            unit = game_state.units.get(unit_id)
            if not unit:
                logger.warning("Unit %s for agent %s missing in game state", unit_id, agent.id)
                continue
            recon_units.append(unit)

        if not recon_units:
            logger.info("Agent %s has no units for recon", agent.id)
            return []

        for unit in recon_units:
            recon_range = self._get_unit_recon_range(unit.type)
            distance = unit.position.distance_to(decision.target)
            if distance <= recon_range:
                actions.append({
                    "type": "recon",
                    "unit_id": unit.id,
                    "target": decision.target,
                    "range": recon_range,
                })
            else:
                logger.info(
                    "Recon validation failed for %s: distance %s exceeds range %s",
                    unit.id,
                    distance,
                    recon_range,
                )

        return actions

    def _resolve_support_request(self, decision: Decision, game_state: GameState) -> List[Dict]:
        agent = game_state.agents.get(decision.agent_id)
        if not agent:
            logger.error("Agent %s not found for REQUEST_SUPPORT decision", decision.agent_id)
            return []

        return [{
            "type": "support_request",
            "agent_id": agent.id,
            "units": list(agent.units_under_command),
            "target": decision.target,
            "confidence": decision.confidence,
            "recipient": agent.superior,
        }]

    def _resolve_defend(self, decision: Decision, game_state: GameState) -> List[Dict]:
        agent = game_state.agents.get(decision.agent_id)
        if not agent:
            logger.error("Agent %s not found for DEFEND decision", decision.agent_id)
            return []

        actions: List[Dict] = []
        for unit_id in agent.units_under_command:
            unit = game_state.units.get(unit_id)
            if not unit:
                logger.warning("Unit %s for agent %s missing in game state", unit_id, agent.id)
                continue
            actions.append({
                "type": "defend",
                "unit_id": unit.id,
                "position": unit.position,
            })
        return actions

    def _get_unit_movement_range(self, unit_type: UnitType) -> int:
        """Returns the base movement range from the design document."""
        if unit_type == UnitType.INFANTRY:
            return 2
        if unit_type == UnitType.ARMOR:
            return 4
        if unit_type == UnitType.RECON:
            return 6
        return 1  # Default for other types like ARTILLERY

    def _get_unit_attack_range(self, unit_type: UnitType) -> int:
        if unit_type == UnitType.ARTILLERY:
            return 3
        if unit_type == UnitType.RECON:
            return 2
        if unit_type == UnitType.ARMOR:
            return 2
        return 1

    def _get_unit_recon_range(self, unit_type: UnitType) -> int:
        if unit_type == UnitType.RECON:
            return 5
        if unit_type == UnitType.ARMOR:
            return 3
        return 2