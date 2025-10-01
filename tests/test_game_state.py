import unittest

from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import Position


class TestGameStateFromScenario(unittest.TestCase):
    def test_from_scenario_builds_full_state(self):
        scenario_data = {
            'map': {
                'size': {'x': 5, 'y': 5},
                'terrain': [
                    {'pos': {'x': 1, 'y': 1}, 'type': 'town', 'cover': 0.6},
                    {'pos': {'x': 2, 'y': 2}, 'type': 'forest', 'movement_cost': 1.4},
                ],
            },
            'scenario': {
                'victory_conditions': [{'type': 'territorial', 'target': {'x': 1, 'y': 1}}],
            },
            'forces': {
                'blue': {
                    'command_structure': {
                        'strategic': [
                            {'id': 'GEN_BLUE', 'name': 'General Blue', 'personality': 'balanced'},
                        ],
                        'tactical': [
                            {
                                'id': 'LT_BLUE',
                                'name': 'Lieutenant Blue',
                                'personality': 'aggressive',
                                'superior': 'GEN_BLUE',
                            }
                        ],
                    },
                    'units': [
                        {
                            'id': 'BLUE_INF',
                            'type': 'infantry',
                            'position': {'x': 1, 'y': 1},
                            'strength': 0.9,
                            'morale': 0.8,
                            'supply': 1.0,
                            'commander': 'LT_BLUE',
                        }
                    ],
                }
            },
            'friction_settings': {'base_probability': 0.1},
            'initial_conditions': {'weather': 'rain', 'time_of_day': '1200'},
        }

        game_state = GameState.from_scenario(scenario_data)

        self.assertEqual(game_state.map_size, (5, 5))
        self.assertEqual(game_state.weather, 'rain')
        self.assertIn('GEN_BLUE', game_state.agents)
        self.assertIn('LT_BLUE', game_state.agents)
        self.assertIn('BLUE_INF', game_state.units)
        self.assertIn('GEN_BLUE', game_state.blue_agents)
        self.assertIn('LT_BLUE', game_state.blue_agents)

        town_pos = Position(1, 1)
        self.assertEqual(game_state.terrain[town_pos], 'town')
        self.assertEqual(game_state.terrain_properties[town_pos]['type'], 'town')

        lieutenant = game_state.agents['LT_BLUE']
        self.assertIn('BLUE_INF', lieutenant.units_under_command)

        self.assertEqual(game_state.victory_conditions[0]['type'], 'territorial')


if __name__ == '__main__':
    unittest.main()
