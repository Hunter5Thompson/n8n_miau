import logging
from typing import Dict, List, Any
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import TurnResult
from kriegsspiel.review.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class AARAgent:
    """
    After-Action Review (AAR) Agent.
    Collects data each turn and generates a final report at the end of the game.
    """
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.report_generator = ReportGenerator()
        logger.info("AARAgent initialized.")

    def record_turn(self, turn_number: int, turn_result: TurnResult, metrics: Dict[str, float]):
        """
        Records the results and metrics of a single turn.

        Args:
            turn_number: The number of the turn being recorded.
            turn_result: The TurnResult object from the TurnManager.
            metrics: The dictionary of metrics from the Evaluator.
        """
        self.history.append({
            "turn": turn_number,
            "result": turn_result,
            "metrics": metrics,
        })
        logger.debug(f"AARAgent recorded data for turn {turn_number}.")

    def generate_final_report(self, game_state: GameState) -> str:
        """
        Generates a final, comprehensive AAR using all recorded history.

        Args:
            game_state: The final GameState of the simulation.

        Returns:
            A formatted string containing the final report.
        """
        logger.info("Generating final AAR.")
        return self.report_generator.generate_final_report(game_state, self.history)

    def generate_turn_summary(self, turn_number: int) -> str:
        """
        Generates a text report for a specific turn from history.
        """
        turn_data = next((item for item in self.history if item["turn"] == turn_number), None)
        if not turn_data:
            return f"No data available for turn {turn_number}."

        # Extract significant events for the report (simplified)
        events = []
        if turn_data["result"].combat_results:
            events.append(f"{len(turn_data['result'].combat_results)} combat(s) occurred.")
        if turn_data["result"].friction_events:
            events.append(f"{len(turn_data['result'].friction_events)} friction event(s) occurred.")

        return self.report_generator.generate_turn_report(
            turn_number,
            turn_data["metrics"],
            events
        )