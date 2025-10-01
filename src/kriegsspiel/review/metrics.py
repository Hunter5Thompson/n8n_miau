import logging
from typing import Dict
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import UnitType, TurnResult, Action

logger = logging.getLogger(__name__)

def compute_intel_utilization(game_state: GameState, turn_result: TurnResult) -> float:
    """Measure how many targeted decisions use fresh intelligence."""

    targeted_decisions = [d for d in turn_result.decisions if d.target]
    if not targeted_decisions:
        return 0.0

    phase_details = getattr(turn_result, 'phase_details', {}) or {}
    intel_phase = phase_details.get('intelligence', {}) if isinstance(phase_details, dict) else {}
    observations = intel_phase.get('observations', {}) if isinstance(intel_phase, dict) else {}

    recent_enemy_positions = set()
    for obs in observations.values():
        for pos, _, confidence in getattr(obs, 'enemy_positions', []):
            if confidence >= 0.5:
                recent_enemy_positions.add(pos)

    if not recent_enemy_positions:
        return 0.0

    relevant_actions = {Action.MOVE, Action.ATTACK, Action.RECON}
    informed = sum(
        1
        for decision in targeted_decisions
        if decision.action in relevant_actions and decision.target in recent_enemy_positions
    )

    return informed / len(targeted_decisions)

def compute_overextension(game_state: GameState, turn_result: TurnResult) -> float:
    """Compute how far blue units operate from friendly towns (supply hubs)."""

    friendly_towns = [
        pos for pos, terrain in game_state.terrain.items()
        if terrain == 'town'
    ]

    blue_agents = getattr(game_state, 'blue_agents', set())
    player_units = [
        unit for unit in game_state.units.values()
        if unit.commander in blue_agents and unit.type != UnitType.ARTILLERY
    ]

    if not friendly_towns or not player_units:
        return 0.0

    total_distance = 0.0
    for unit in player_units:
        min_dist_to_hub = min(unit.position.distance_to(town) for town in friendly_towns)
        total_distance += min_dist_to_hub

    avg_distance = total_distance / len(player_units)

    return min(1.0, avg_distance / 10.0)

def compute_ler(game_state: GameState, turn_result: TurnResult) -> float:
    """Compute the loss exchange ratio for the blue side."""

    if not turn_result.combat_results:
        return 0.5

    blue_agents = getattr(game_state, 'blue_agents', set())
    own_losses = 0.0
    enemy_losses = 0.0

    for combat in turn_result.combat_results:
        result = combat.get('result')
        if not result:
            continue

        attacker = game_state.units.get(combat.get('attacker'))
        defender = game_state.units.get(combat.get('defender'))
        if not attacker or not defender:
            continue

        attacker_is_blue = attacker.commander in blue_agents
        defender_is_blue = defender.commander in blue_agents

        if attacker_is_blue and not defender_is_blue:
            own_losses += result.attacker_losses
            enemy_losses += result.defender_losses
        elif defender_is_blue and not attacker_is_blue:
            own_losses += result.defender_losses
            enemy_losses += result.attacker_losses

    if own_losses == 0 and enemy_losses == 0:
        return 0.5
    if own_losses == 0:
        return 1.0

    ratio = enemy_losses / own_losses
    return max(0.0, min(1.0, ratio))

def compute_order_staleness(game_state: GameState, turn_result: TurnResult) -> float:
    """
    Computes the average delay of messages delivered this turn.
    Normalizes the delay to a 0-1 scale.
    """
    if not turn_result.messages_delivered:
        return 0.0

    total_delay = 0
    for msg in turn_result.messages_delivered:
        delay = msg.turn_received - msg.turn_sent
        total_delay += delay

    avg_delay = total_delay / len(turn_result.messages_delivered)

    # Normalize the score. A delay of 3+ turns is considered very stale.
    normalized_staleness = min(1.0, avg_delay / 3.0)
    return normalized_staleness