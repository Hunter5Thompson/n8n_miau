import unittest
from unittest.mock import MagicMock, patch
from collections import namedtuple

# Use a simple structure for mocking TurnResult and Message
MockMessage = namedtuple('MockMessage', ['turn_sent', 'turn_received'])
MockTurnResult = namedtuple('MockTurnResult', ['messages_delivered', 'combat_results', 'decisions', 'friction_events'])

from kriegsspiel.review.evaluator import Evaluator
from kriegsspiel.review.metrics import compute_order_staleness
from kriegsspiel.core.game_state import GameState

class TestReviewModule(unittest.TestCase):

    def setUp(self):
        """Set up a new Evaluator for each test."""
        self.evaluator = Evaluator()
        self.mock_game_state = MagicMock(spec=GameState)

    def test_evaluator_returns_dict_on_success(self):
        """Ensure the evaluator returns a dictionary with all metric keys."""
        mock_turn_result = MockTurnResult(messages_delivered=[], combat_results=[], decisions=[], friction_events=[])

        metrics = self.evaluator.evaluate(self.mock_game_state, mock_turn_result)

        self.assertIsInstance(metrics, dict)
        expected_keys = ["intel_utilization", "overextension", "loss_exchange_ratio", "order_staleness"]
        for key in expected_keys:
            self.assertIn(key, metrics)
            self.assertIsInstance(metrics[key], float)

    def test_evaluator_handles_exceptions_gracefully(self):
        """Ensure the evaluator returns default values and logs an error if a metric fails."""
        with patch('kriegsspiel.review.evaluator.compute_intel_utilization', side_effect=Exception("Test Error")):
            mock_turn_result = MockTurnResult(messages_delivered=[], combat_results=[], decisions=[], friction_events=[])

            # The logger is configured to output to console, so we don't need to capture logs here
            # unless we want to assert specific log messages.
            metrics = self.evaluator.evaluate(self.mock_game_state, mock_turn_result)

            self.assertEqual(metrics["intel_utilization"], 0.0)
            self.assertEqual(metrics["loss_exchange_ratio"], 0.5)

    def test_suggest_tweaks_logic(self):
        """Test the logic for suggesting policy tweaks."""
        # Case 1: Low intel utilization should trigger a recon bias increase
        low_intel_metrics = {"intel_utilization": 0.2}
        tweaks = self.evaluator.suggest_tweaks(low_intel_metrics)
        self.assertIn("recon_bias", tweaks["policy_weights"])
        self.assertGreater(tweaks["policy_weights"]["recon_bias"], 0)

        # Case 2: High overextension should trigger an attack bias decrease
        high_overextension_metrics = {"overextension": 0.7}
        tweaks = self.evaluator.suggest_tweaks(high_overextension_metrics)
        self.assertIn("attack_bias", tweaks["policy_weights"])
        self.assertLess(tweaks["policy_weights"]["attack_bias"], 0)

        # Case 3: Good metrics should result in no tweaks
        good_metrics = {"intel_utilization": 0.9, "overextension": 0.1}
        tweaks = self.evaluator.suggest_tweaks(good_metrics)
        self.assertEqual(len(tweaks["policy_weights"]), 0)

    def test_compute_order_staleness(self):
        """Test the order staleness metric calculation."""
        # No messages, staleness should be 0
        turn_result_none = MockTurnResult(messages_delivered=[], combat_results=[], decisions=[], friction_events=[])
        staleness = compute_order_staleness(self.mock_game_state, turn_result_none)
        self.assertEqual(staleness, 0.0)

        # Messages with a 1-turn delay
        messages_one_delay = [MockMessage(turn_sent=1, turn_received=2), MockMessage(turn_sent=2, turn_received=3)]
        turn_result_one = MockTurnResult(messages_delivered=messages_one_delay, combat_results=[], decisions=[], friction_events=[])
        staleness = compute_order_staleness(self.mock_game_state, turn_result_one)
        # Avg delay = 1. Normalized = 1 / 3 = 0.333...
        self.assertAlmostEqual(staleness, 1.0 / 3.0)

        # Messages with a >3 turn delay should clamp to 1.0
        messages_high_delay = [MockMessage(turn_sent=1, turn_received=5)] # 4 turn delay
        turn_result_high = MockTurnResult(messages_delivered=messages_high_delay, combat_results=[], decisions=[], friction_events=[])
        staleness = compute_order_staleness(self.mock_game_state, turn_result_high)
        # Avg delay = 4. Normalized = min(1.0, 4/3) = 1.0
        self.assertEqual(staleness, 1.0)

if __name__ == '__main__':
    unittest.main()