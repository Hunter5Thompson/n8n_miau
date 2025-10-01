import unittest
from unittest.mock import MagicMock

# It's better to import the concrete classes for instantiation
from kriegsspiel.core.types import Decision, Position, Action, UnitType, Rank
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.units import Unit
from kriegsspiel.agents.base_agent import BaseAgent
from kriegsspiel.decisions.action_resolver import ActionResolver

# Mock the abstract BaseAgent to instantiate it for testing
class MockAgent(BaseAgent):
    def __init__(self, agent_id, name, rank, units_under_command=None):
        # Mock personality as it's required by the BaseAgent constructor
        mock_personality = MagicMock()
        super().__init__(agent_id=agent_id, name=name, rank=rank, personality=mock_personality)
        if units_under_command:
            self.units_under_command = units_under_command

    def decide(self, game_state) -> Decision:
        pass # Not needed for this test

    def process_orders(self, orders: str) -> None:
        pass # Not needed for this test

class TestActionResolver(unittest.TestCase):

    def setUp(self):
        """Set up a common game state for all tests."""
        self.resolver = ActionResolver()
        self.game_state = GameState(map_size=(10, 10))

        # Create a commander agent
        self.commander = MockAgent(
            agent_id="COL_MUELLER",
            name="Colonel Müller",
            rank=Rank.OPERATIONAL,
            units_under_command=["1ST_INF_BATTALION"]
        )
        self.game_state.add_agent(self.commander)
        self.game_state.blue_agents.add(self.commander.id)

        # Create a unit for that commander
        self.unit = Unit(
            id="1ST_INF_BATTALION",
            type=UnitType.INFANTRY, # Movement range = 2
            position=Position(x=2, y=2),
            strength=1.0,
            morale=1.0,
            supply=1.0,
            commander="COL_MUELLER"
        )
        self.game_state.add_unit(self.unit)

        # Define some terrain with costs
        self.forest_pos = Position(x=2, y=3)
        self.river_pos = Position(x=3, y=2)
        self.game_state.terrain_properties[self.forest_pos] = {"type": "forest", "movement_cost": 1.5}
        self.game_state.terrain_properties[self.river_pos] = {"type": "river", "movement_cost": 999}

        # Default enemy commander for attack tests
        self.enemy_commander_id = "COL_IVANOV"

    def test_resolve_valid_move(self):
        """Test resolving a valid MOVE decision to an open field."""
        target_pos = Position(x=3, y=3) # Distance = 2, cost = 1.0 per tile
        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.MOVE,
            target=target_pos,
            reasoning="Advance",
            confidence=0.9
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "move")
        self.assertEqual(actions[0]["unit_id"], "1ST_INF_BATTALION")
        self.assertEqual(actions[0]["to"], target_pos)

    def test_resolve_invalid_move_out_of_range(self):
        """Test a move that is beyond the unit's maximum range."""
        target_pos = Position(x=5, y=5) # Distance = 6, too far for infantry (range 2)
        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.MOVE,
            target=target_pos,
            reasoning="Flank",
            confidence=0.8
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 0, "Should not generate an action for a move out of range.")

    def test_resolve_invalid_move_high_terrain_cost(self):
        """Test a move to an adjacent but impassable tile."""
        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.MOVE,
            target=self.river_pos, # Adjacent, but cost is 999
            reasoning="Cross river",
            confidence=0.7
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 0, "Should not generate an action for a move into impassable terrain.")

    def test_resolve_valid_move_into_costly_terrain(self):
        """Test a valid move into terrain that costs more but is within range."""
        # Infantry range is 2. Forest is at (2,3), distance is 1. Cost is 1.5. Total cost = 1 * 1.5 = 1.5.
        # This is within the max range of 2.
        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.MOVE,
            target=self.forest_pos,
            reasoning="Take cover",
            confidence=0.95
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["unit_id"], "1ST_INF_BATTALION")
        self.assertEqual(actions[0]["to"], self.forest_pos)

    def test_resolve_attack_generates_actions(self):
        """Attack decisions should translate to attack actions for in-range units."""
        enemy_position = Position(x=3, y=2)
        enemy_unit = Unit(
            id="RED_INF_1",
            type=UnitType.INFANTRY,
            position=enemy_position,
            strength=0.8,
            morale=0.7,
            supply=0.9,
            commander=self.enemy_commander_id,
        )
        self.game_state.add_unit(enemy_unit)

        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.ATTACK,
            target=enemy_position,
            reasoning="Engage enemy",
            confidence=0.8,
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["type"], "attack")
        self.assertEqual(actions[0]["target"], enemy_position)

    def test_resolve_attack_out_of_range(self):
        """Units should not attack targets outside their attack range."""
        distant_target = Position(x=7, y=7)
        enemy_unit = Unit(
            id="RED_INF_2",
            type=UnitType.INFANTRY,
            position=distant_target,
            strength=0.8,
            morale=0.7,
            supply=0.9,
            commander=self.enemy_commander_id,
        )
        self.game_state.add_unit(enemy_unit)

        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.ATTACK,
            target=distant_target,
            reasoning="Engage distant enemy",
            confidence=0.6,
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertEqual(len(actions), 0)

    def test_resolve_recon_requires_recon_unit(self):
        """Recon actions should be generated for recon-capable units within range."""
        scout = Unit(
            id="SCOUT_TROOP",
            type=UnitType.RECON,
            position=Position(x=1, y=2),
            strength=1.0,
            morale=1.0,
            supply=1.0,
            commander="COL_MUELLER",
        )
        self.game_state.add_unit(scout)
        self.commander.units_under_command.append(scout.id)

        recon_target = Position(x=3, y=3)
        decision = Decision(
            agent_id="COL_MUELLER",
            action=Action.RECON,
            target=recon_target,
            reasoning="Scout ahead",
            confidence=0.7,
        )

        actions = self.resolver.resolve(decision, self.game_state)

        self.assertTrue(any(action["unit_id"] == scout.id for action in actions))

if __name__ == '__main__':
    unittest.main()