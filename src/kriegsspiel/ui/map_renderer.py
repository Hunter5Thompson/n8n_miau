import logging
from collections import defaultdict
from typing import Dict, Tuple
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import Position, UnitType

logger = logging.getLogger(__name__)

TERRAIN_SYMBOLS = {
    "open": ".",
    "forest": "#",
    "hill": "^",
    "river": "~",
    "road": "=",
    "town": "*",
}

UNIT_SYMBOLS = {
    UnitType.INFANTRY: "I",
    UnitType.ARMOR: "A",
    UnitType.RECON: "R",
    UnitType.ARTILLERY: "T",
}

class MapRenderer:
    """Renders the game state as an ASCII map."""

    def render(self, game_state: GameState) -> str:
        """
        Generates a string representation of the current game map.

        Args:
            game_state: The current GameState to render.

        Returns:
            A formatted string representing the map.
        """
        if not game_state.map_size:
            logger.warning("Map size not set in game state. Cannot render map.")
            return "Map data is unavailable."

        width, height = game_state.map_size
        grid = [["." for _ in range(width)] for _ in range(height)]

        # 1. Draw terrain
        for pos, props in game_state.terrain_properties.items():
            if 0 <= pos.x < width and 0 <= pos.y < height:
                terrain_type = props.get("type", "open")
                grid[pos.y][pos.x] = TERRAIN_SYMBOLS.get(terrain_type, "?")

        # 2. Draw units
        unit_positions = defaultdict(list)
        for unit in game_state.units.values():
            if unit.is_combat_effective():
                 unit_positions[unit.position].append(unit)

        for pos, units_on_tile in unit_positions.items():
            if 0 <= pos.x < width and 0 <= pos.y < height:
                if len(units_on_tile) > 1:
                    grid[pos.y][pos.x] = str(len(units_on_tile))
                elif units_on_tile:
                    unit_type = units_on_tile[0].type
                    grid[pos.y][pos.x] = UNIT_SYMBOLS.get(unit_type, "U")

        # 3. Format the final string with coordinates
        map_str_lines = []
        header = "    " + " ".join(f"{i:<1}" for i in range(width))
        map_str_lines.append(header)
        map_str_lines.append("   " + "-" * (width * 2))

        for y, row in enumerate(grid):
            map_str_lines.append(f"{y:>2} | {' '.join(row)}")

        map_str_lines.append("\nLegend: .=open, #=forest, ^=hill, ~=river, ==road, *=town")
        map_str_lines.append("        I=Inf, A=Armor, R=Recon, T=Arty, [n]=Stack")

        return "\n".join(map_str_lines)