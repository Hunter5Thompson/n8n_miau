import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

from kriegsspiel.ui.text_interface import TextInterface
from kriegsspiel.ui.map_renderer import MapRenderer
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import Position, UnitType, TurnResult
from kriegsspiel.core.units import Unit

class TestUIModule(unittest.TestCase):

    def setUp(self):
        """Set up UI components for each test."""
        self.text_interface = TextInterface()
        self.map_renderer = MapRenderer()
        self.mock_game_state = MagicMock(spec=GameState)
        self.mock_game_state.turn = 1
        self.mock_game_state.weather = "Clear"
        self.mock_game_state.time_of_day = "0800"
        self.mock_game_state.blue_agents = {'unit1'}
        self.mock_game_state.units = {
            'unit1': MagicMock(spec=Unit, morale=0.9, supply=0.95, is_combat_effective=lambda: True)
        }

    @patch('sys.stdout', new_callable=StringIO)
    def test_text_interface_display_header(self, mock_stdout):
        """Test that the turn header displays without errors."""
        self.text_interface.display_turn_header(self.mock_game_state)
        output = mock_stdout.getvalue()
        self.assertIn("TURN 1", output)
        self.assertIn("Weather: Clear", output)
        self.assertIn("Blue Avg Morale: 0.90", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_text_interface_display_results_handles_missing_data(self, mock_stdout):
        """Test that display_results runs without errors when turn_result has missing fields."""
        # Create a TurnResult with some attributes missing
        turn_result = MagicMock(spec=TurnResult)
        # By using a MagicMock with a spec, attributes that are not explicitly set will not exist.

        try:
            self.text_interface.display_results(turn_result)
        except Exception as e:
            self.fail(f"display_results raised an exception with missing data: {e}")

        output = mock_stdout.getvalue()
        self.assertIn("--- Turn Results ---", output) # Check that it at least prints the header

    def test_map_renderer_runs_without_error(self):
        """Test that the map renderer can render a basic map without crashing."""
        game_state = GameState(map_size=(5, 5))
        game_state.terrain_properties[Position(1, 1)] = {"type": "forest"}
        game_state.units['inf1'] = Unit(id='inf1', type=UnitType.INFANTRY, position=Position(2,2), strength=1.0, morale=1.0, supply=1.0, commander='cmd1')

        try:
            map_str = self.map_renderer.render(game_state)
            self.assertIsInstance(map_str, str)
            self.assertIn("#", map_str) # Check for forest symbol
            self.assertIn("I", map_str) # Check for infantry symbol
        except Exception as e:
            self.fail(f"MapRenderer.render raised an exception: {e}")

    def test_map_renderer_handles_no_map_size(self):
        """Test that the map renderer handles game_state without a map_size gracefully."""
        game_state = GameState(map_size=None)
        map_str = self.map_renderer.render(game_state)
        self.assertEqual(map_str, "Map data is unavailable.")


if __name__ == '__main__':
    unittest.main()