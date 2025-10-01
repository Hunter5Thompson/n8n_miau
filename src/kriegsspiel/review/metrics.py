import logging
from typing import Dict, List, Any
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import UnitType, TurnResult

logger = logging.getLogger(__name__)

def compute_intel_utilization(game_state: GameState, turn_result: TurnResult) -> float:
    """
    Computes the utilization of recent intelligence.
    Placeholder: Returns a static value for now. A real implementation would
    check if actions were based on observations <= 2 turns old.
    """
    # This is a placeholder. A real implementation would require linking
    # decisions to the specific observations that prompted them.
    return 0.75

def compute_overextension(game_state: GameState, turn_result: TurnResult) -> float:
    """
    Computes the average distance of units to their nearest friendly supply hub (town).
    Normalizes the distance to a 0-1 scale, where > 0.6 is a warning.
    """
    friendly_towns = [
        pos for pos, props in game_state.terrain_properties.items()
        if props.get("type") == "town"
    ]

    # This metric is calculated for a specific side, let's assume 'blue' for now.
    # A full implementation would need to know which side is being evaluated.
    player_units = [u for u in game_state.units.values() if u.id in game_state.blue_agents] # Simplified assumption

    if not friendly_towns or not player_units:
        return 0.0

    total_distance = 0
    for unit in player_units:
        if unit.type != UnitType.ARTILLERY: # Exclude static units
             min_dist_to_hub = min(unit.position.distance_to(town_pos) for town_pos in friendly_towns)
             total_distance += min_dist_to_hub

    avg_distance = total_distance / len(player_units) if player_units else 0.0

    # Normalize the score. Let's assume a critical distance is ~10 units away.
    # Anything beyond that is highly overextended.
    normalized_score = min(1.0, avg_distance / 10.0)
    return normalized_score

def compute_ler(game_state: GameState, turn_result: TurnResult) -> float:
    """
    Computes the Loss Exchange Ratio.
    A value > 0.5 is good for the player, < 0.5 is bad.
    """
    own_losses = 0.0
    enemy_losses = 0.0

    # Assuming turn_result.combat_results is a list of dicts with casualty info
    if not turn_result.combat_results:
        return 0.5 # No combat, neutral ratio

    for combat in turn_result.combat_results:
        # A real implementation would need to distinguish friend from foe
        # For now, we'll need to make assumptions.
        # This part of the code is highly dependent on the final CombatResult structure.
        pass # Placeholder

    # Placeholder logic until CombatResult is finalized
    # For now, returning a static value to avoid errors.
    return 0.6 # Placeholder

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