import logging
from typing import Dict
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import TurnResult
from kriegsspiel.review.metrics import (
    compute_intel_utilization,
    compute_overextension,
    compute_ler,
    compute_order_staleness,
)

logger = logging.getLogger(__name__)

class Evaluator:
    """Compute turn metrics and propose minor policy tweaks."""

    def evaluate(self, game_state: GameState, turn_result: TurnResult) -> Dict[str, float]:
        """
        Calculates and returns a dictionary of performance metrics for a given turn.
        """
        try:
            m = {
                "intel_utilization": compute_intel_utilization(game_state, turn_result),
                "overextension": compute_overextension(game_state, turn_result),
                "loss_exchange_ratio": compute_ler(game_state, turn_result),
                "order_staleness": compute_order_staleness(game_state, turn_result),
            }
            logger.info("Evaluator completed. Metrics: %s", m)
            return m
        except Exception as exc:
            logger.exception("Evaluator failed to compute metrics: %s", exc)
            # Return default values on failure to avoid crashing the simulation
            return {
                "intel_utilization": 0.0,
                "overextension": 0.0,
                "loss_exchange_ratio": 0.5, # Neutral
                "order_staleness": 0.0,
            }

    def suggest_tweaks(self, metrics: Dict[str, float]) -> Dict:
        """
        Suggests simple policy adjustments based on the turn's metrics.
        """
        tweaks = {"policy_weights": {}}
        if metrics.get("intel_utilization", 1.0) < 0.4:
            tweaks["policy_weights"]["recon_bias"] = +0.1
            logger.info("Suggesting tweak: Increase recon_bias due to low intel utilization.")
        if metrics.get("overextension", 0.0) > 0.6:
            tweaks["policy_weights"]["attack_bias"] = -0.1
            logger.info("Suggesting tweak: Decrease attack_bias due to overextension.")
        return tweaks