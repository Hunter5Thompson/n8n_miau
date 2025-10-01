from dataclasses import dataclass
from typing import List, Tuple
from ..core.types import Position
from ..core.units import Unit

@dataclass
class CombatResult:
    attacker_losses: float
    defender_losses: float
    attacker_morale_impact: float
    defender_morale_impact: float
    terrain_effect: float
    tactical_surprise: bool
    description: str

class CombatResolver:
    """
    Kampfsystem mit taktischen Feinheiten
    
    Berücksichtigt:
    - Materialqualität und Munition
    - Taktisches Verhalten (statisch vs. mobil)
    - Gelände und Deckung
    - Überraschung und Aufklärung
    - Ausbildungsstand
    """
    
    def __init__(self):
        self.combat_history = {}  # Unit-ID -> letzte Position/Aktion
        
    def resolve_combat(
        self,
        attacker: Unit,
        defender: Unit,
        terrain: dict,
        attacker_detected: bool,
        defender_detected: bool
    ) -> CombatResult:
        """Hauptkampfauflösung"""
        
        # 1. Basisstärke berechnen
        attacker_power = self._calculate_combat_power(attacker)
        defender_power = self._calculate_combat_power(defender)
        
        # 2. Gelände-Modifikatoren
        terrain_mod = self._get_terrain_modifier(defender.position, terrain)
        defender_power *= terrain_mod
        
        # 3. Taktische Situation
        tactical_mod = self._evaluate_tactical_situation(
            attacker, defender, attacker_detected, defender_detected
        )
        attacker_power *= tactical_mod['attacker']
        defender_power *= tactical_mod['defender']
        
        # 4. Beweglichkeit und Aufklärung
        mobility_factor = self._calculate_mobility_advantage(attacker, defender)
        
        # 5. Munitions- und Materialqualität
        equipment_factor = self._evaluate_equipment_quality(attacker, defender)
        
        # 6. Kampfauflösung
        power_ratio = attacker_power / max(defender_power, 0.1)
        
        attacker_losses = self._calculate_losses(
            base_rate=0.1,
            power_ratio=1/power_ratio,
            quality=defender.equipment_quality,
            mobility=mobility_factor['defender']
        )
        
        defender_losses = self._calculate_losses(
            base_rate=0.15,  # Verteidiger verlieren weniger
            power_ratio=power_ratio,
            quality=attacker.equipment_quality,
            mobility=mobility_factor['attacker']
        )
        
        # 7. Morale-Auswirkungen
        morale_impact = self._calculate_morale_impact(
            attacker_losses, defender_losses, tactical_mod
        )
        
        # 8. Combat History aktualisieren (für Mobility-Tracking)
        self._update_combat_history(attacker, defender)
        
        return CombatResult(
            attacker_losses=attacker_losses,
            defender_losses=defender_losses,
            attacker_morale_impact=morale_impact['attacker'],
            defender_morale_impact=morale_impact['defender'],
            terrain_effect=terrain_mod,
            tactical_surprise=tactical_mod.get('surprise', False),
            description=self._generate_combat_description(
                attacker, defender, power_ratio, tactical_mod
            )
        )
    
    def _calculate_combat_power(self, unit: Unit) -> float:
        """Basiskampfkraft"""
        base = unit.strength * unit.morale * unit.supply
        
        # Equipment-Multiplikator
        equipment_mult = getattr(unit, 'equipment_quality', 0.7)
        
        return base * equipment_mult
    
    def _get_terrain_modifier(self, position: Position, terrain: dict) -> float:
        """Gelände-Vorteil für Verteidiger"""
        terrain_type = terrain.get(position, 'open')
        
        modifiers = {
            'open': 1.0,
            'forest': 1.4,
            'hill': 1.3,
            'town': 1.6,
            'fortified': 2.0
        }
        return modifiers.get(terrain_type, 1.0)
    
    def _evaluate_tactical_situation(
        self,
        attacker: Unit,
        defender: Unit,
        attacker_detected: bool,
        defender_detected: bool
    ) -> dict:
        """
        Taktische Vorteile/Nachteile
        
        Kernmechanik: Bewegung und Täuschung sind überlebenswichtig
        """
        result = {
            'attacker': 1.0,
            'defender': 1.0,
            'surprise': False
        }
        
        # Überraschungseffekt
        if not attacker_detected and defender_detected:
            result['attacker'] *= 1.5
            result['surprise'] = True
        elif attacker_detected and not defender_detected:
            result['defender'] *= 1.3
        
        # Beweglichkeit aus History
        attacker_mobility = self._get_unit_mobility_score(attacker.id)
        defender_mobility = self._get_unit_mobility_score(defender.id)
        
        # Statische Einheiten = leichte Ziele
        if defender_mobility < 0.3:  # Kaum bewegt
            result['attacker'] *= 1.3
            result['defender'] *= 0.8  # Leichter zu treffen
        
        if attacker_mobility > 0.7:  # Sehr mobil
            result['attacker'] *= 1.2  # Schwerer zu treffen
        
        return result
    
    def _calculate_mobility_advantage(
        self,
        attacker: Unit,
        defender: Unit
    ) -> dict:
        """
        Mobilität auf dem Gefechtsfeld
        
        Panzer die sich bewegen vs. statische Stellung
        """
        attacker_moves = self._count_recent_moves(attacker.id, turns=3)
        defender_moves = self._count_recent_moves(defender.id, turns=3)
        
        # Normalisiere auf 0-1
        attacker_mobility = min(1.0, attacker_moves / 3.0)
        defender_mobility = min(1.0, defender_moves / 3.0)
        
        return {
            'attacker': attacker_mobility,
            'defender': defender_mobility
        }
    
    def _evaluate_equipment_quality(
        self,
        attacker: Unit,
        defender: Unit
    ) -> dict:
        """
        Materialqualität und Munitionszustand
        
        Wichtig: Schlechte Munition reduziert Effektivität massiv
        """
        attacker_eq = getattr(attacker, 'equipment_quality', 0.8)
        defender_eq = getattr(defender, 'equipment_quality', 0.8)
        
        # Munitionszustand (falls vorhanden)
        attacker_ammo = getattr(attacker, 'ammunition_quality', 1.0)
        defender_ammo = getattr(defender, 'ammunition_quality', 1.0)
        
        # Sabotage/mindere Qualität hat drastische Auswirkung
        if attacker_ammo < 0.5:  # Sabotierte Munition
            attacker_eq *= 0.4  # 60% Effektivitätsverlust!
        
        return {
            'attacker': attacker_eq * attacker_ammo,
            'defender': defender_eq * defender_ammo
        }
    
    def _calculate_losses(
        self,
        base_rate: float,
        power_ratio: float,
        quality: float,
        mobility: float
    ) -> float:
        """
        Verlustberechnung mit allen Faktoren
        """
        # Grundverluste
        losses = base_rate * power_ratio
        
        # Qualität reduziert Verluste
        losses *= (1.0 - (quality * 0.3))
        
        # Mobilität reduziert Verluste (bewegte Ziele schwerer zu treffen)
        losses *= (1.0 - (mobility * 0.4))
        
        return min(1.0, max(0.0, losses))
    
    def _calculate_morale_impact(
        self,
        attacker_losses: float,
        defender_losses: float,
        tactical_mod: dict
    ) -> dict:
        """Moral-Auswirkungen"""
        
        # Verluste senken Moral
        attacker_morale = -attacker_losses * 0.5
        defender_morale = -defender_losses * 0.5
        
        # Überraschung schadet Moral extra
        if tactical_mod.get('surprise'):
            defender_morale -= 0.2
        
        # Erfolgreiche Verteidigung hebt Moral
        if defender_losses < attacker_losses * 0.5:
            defender_morale += 0.1
        
        return {
            'attacker': attacker_morale,
            'defender': defender_morale
        }
    
    def _update_combat_history(self, attacker: Unit, defender: Unit):
        """Trackt Bewegungen für Mobility-Score"""
        if attacker.id not in self.combat_history:
            self.combat_history[attacker.id] = []
        if defender.id not in self.combat_history:
            self.combat_history[defender.id] = []
        
        self.combat_history[attacker.id].append(attacker.position)
        self.combat_history[defender.id].append(defender.position)
        
        # Behalte nur letzte 5 Positionen
        self.combat_history[attacker.id] = self.combat_history[attacker.id][-5:]
        self.combat_history[defender.id] = self.combat_history[defender.id][-5:]
    
    def _get_unit_mobility_score(self, unit_id: str) -> float:
        """Wie mobil war die Einheit in letzter Zeit?"""
        if unit_id not in self.combat_history:
            return 0.5  # Unbekannt = mittel
        
        positions = self.combat_history[unit_id]
        if len(positions) < 2:
            return 0.5
        
        # Zähle Positionswechsel
        moves = sum(
            1 for i in range(len(positions)-1)
            if positions[i] != positions[i+1]
        )
        
        return moves / len(positions)
    
    def _count_recent_moves(self, unit_id: str, turns: int) -> int:
        """Anzahl Bewegungen in letzten X Turns"""
        if unit_id not in self.combat_history:
            return 0
        
        positions = self.combat_history[unit_id][-turns:]
        return sum(
            1 for i in range(len(positions)-1)
            if positions[i] != positions[i+1]
        )
    
    def _generate_combat_description(
        self,
        attacker: Unit,
        defender: Unit,
        power_ratio: float,
        tactical_mod: dict
    ) -> str:
        """Natürlichsprachliche Beschreibung"""
        
        if tactical_mod.get('surprise'):
            return f"{attacker.id} catches {defender.id} by surprise!"
        
        if power_ratio > 2.0:
            return f"{attacker.id} overwhelms {defender.id}"
        elif power_ratio > 1.5:
            return f"{attacker.id} gains upper hand against {defender.id}"
        elif power_ratio > 0.7:
            return f"{attacker.id} and {defender.id} trade fire evenly"
        else:
            return f"{defender.id} repels {attacker.id}'s attack"