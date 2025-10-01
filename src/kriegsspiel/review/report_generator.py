import logging
from typing import Dict, List, Any
from kriegsspiel.core.game_state import GameState

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates human-readable text reports for turns and final summaries."""

    def generate_turn_report(self, turn: int, metrics: Dict[str, float], events: List[str]) -> str:
        """
        Generates a summary report for a single turn.

        Args:
            turn: The turn number.
            metrics: A dictionary of metrics calculated by the Evaluator.
            events: A list of significant event strings from the turn.

        Returns:
            A formatted string report for the turn.
        """
        report_lines = [
            f"--- AFTER-ACTION REPORT: TURN {turn} ---",
            "1. Key Metrics:",
            f"  - Intel Utilization:   {metrics.get('intel_utilization', 0.0):.2f}",
            f"  - Overextension:       {metrics.get('overextension', 0.0):.2f}",
            f"  - Loss Exchange Ratio: {metrics.get('loss_exchange_ratio', 0.0):.2f}",
            f"  - Order Staleness:     {metrics.get('order_staleness', 0.0):.2f}",
            "",
            "2. Significant Events:",
        ]
        if events:
            for event in events:
                report_lines.append(f"  - {event}")
        else:
            report_lines.append("  - No significant events logged.")

        report_lines.append("-" * 40)
        return "\n".join(report_lines)

    def generate_final_report(self, game_state: GameState, history: List[Dict[str, Any]]) -> str:
        """
        Generates a final summary report for the entire game.

        Args:
            game_state: The final state of the game.
            history: A list of historical turn data (e.g., from an AARAgent).

        Returns:
            A formatted string for the final game report.
        """
        report_lines = [
            "========================================",
            "        FINAL AFTER-ACTION REPORT",
            "========================================",
            f"Scenario: {game_state.scenario_name if hasattr(game_state, 'scenario_name') else 'N/A'}",
            f"Total Turns: {game_state.turn}",
            "",
            "--- Victory Conditions ---"
        ]

        # This part requires victory conditions to be clearly defined in the game state
        # and a check for which side won. This is a placeholder for now.
        is_victory = game_state.is_finished() and game_state.check_victory()
        report_lines.append(f"Game End State: {'VICTORY' if is_victory else 'CEASEFIRE'}")

        # Placeholder for final summary metrics
        report_lines.append("\n--- Overall Performance ---")
        report_lines.append("  - (Metrics summary would be implemented here)")

        report_lines.append("\n--- Log Summary ---")
        if game_state.event_log:
             # Show the last few events
            for event in game_state.event_log[-5:]:
                report_lines.append(f"  - {event}")
        else:
            report_lines.append("  - No events in log.")

        report_lines.append("\n========================================")
        return "\n".join(report_lines)