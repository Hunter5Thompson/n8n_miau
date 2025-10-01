import logging
from typing import Any, Dict
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import TurnResult
from kriegsspiel.ui.map_renderer import MapRenderer

logger = logging.getLogger(__name__)

class TextInterface:
    """Simple CLI renderer for turns, results, and maps."""

    def __init__(self):
        self.map_renderer = MapRenderer()
        logger.info("TextInterface initialized.")

    def display_turn_header(self, game_state: GameState) -> None:
        """Displays a header for the current turn with key information."""
        # Assuming 'blue' is the player side for metrics. This could be parameterized.
        player_units = [
            u for u_id, u in game_state.units.items()
            if u_id in game_state.blue_agents and u.is_combat_effective()
        ]
        avg_morale = sum(u.morale for u in player_units) / len(player_units) if player_units else 0.0
        avg_supply = sum(u.supply for u in player_units) / len(player_units) if player_units else 0.0

        print("=" * 60)
        print(f"TURN {game_state.turn}  |  Weather: {game_state.weather}  |  Time: {game_state.time_of_day}")
        print(f"Blue Avg Morale: {avg_morale:.2f} | Blue Avg Supply: {avg_supply:.2f}")
        print("-" * 60)

    def display_results(self, turn_result: TurnResult) -> None:
        """Displays the results of a completed turn in a structured way."""
        print("\n--- Turn Results ---")

        if hasattr(turn_result, 'decisions') and turn_result.decisions:
            print(f"Decisions made: {len(turn_result.decisions)}")

        if hasattr(turn_result, 'messages_delivered') and turn_result.messages_delivered:
            print("Messages delivered:")
            for m in turn_result.messages_delivered:
                if all(hasattr(m, attr) for attr in ['sender', 'receiver', 'turn_sent', 'turn_received']):
                    print(f"  {m.sender} → {m.receiver} (T{m.turn_sent}→T{m.turn_received})")
                else:
                    logger.debug(f"Skipping malformed message object: {m}")

        if hasattr(turn_result, 'combat_results') and turn_result.combat_results:
            print("Combat:")
            for entry in turn_result.combat_results:
                if isinstance(entry, dict) and all(k in entry for k in ['attacker', 'defender', 'result']):
                    res = entry["result"]
                    print(f"  {entry['attacker']} vs {entry['defender']}: {res.description}")
                else:
                    logger.debug(f"Skipping malformed combat result: {entry}")

        if hasattr(turn_result, 'friction_events') and turn_result.friction_events:
            print("Friction:")
            for ev in turn_result.friction_events:
                if all(hasattr(ev, attr) for attr in ['type', 'description']):
                    print(f"  - {ev.type}: {ev.description}")
                else:
                    logger.debug(f"Skipping malformed friction event: {ev}")
        print("-" * 20 + "\n")

    def display_map(self, game_state: GameState) -> None:
        """Renders and displays the ASCII game map."""
        print("\n--- MAP OVERVIEW ---")
        print(self.map_renderer.render(game_state))
        print("-" * 60 + "\n")