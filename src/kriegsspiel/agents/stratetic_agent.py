from kriegsspiel.agents.base_agent import BaseAgent
from kriegsspiel.agents.personality import Personality
from kriegsspiel.core.types import Rank, Decision, Action, Position
from typing import Optional

class StrategicAgent(BaseAgent):
    """
    Strategische Ebene - Armee/Korps-Kommandeur
    
    Fokus:
    - Gesamtlage
    - Ressourcenverteilung
    - Operative Ziele setzen
    - Koordination zwischen Corps/Divisionen
    """
    
    def __init__(self, agent_id: str, name: str, personality: Personality):
        super().__init__(agent_id, name, Rank.STRATEGIC, personality)
        self.strategic_objective = None
        self.reserve_units = []
        
    def decide(self, game_state) -> Decision:
        """Strategische Entscheidung"""
        
        # 1. Lagebeurteilung auf strategischer Ebene
        situation = self._assess_strategic_situation(game_state)
        
        # 2. Prüfe ob Ziel erreicht
        if self._is_objective_achieved(game_state):
            return self._set_new_objective(game_state)
        
        # 3. Prüfe ob Untergebene Unterstützung brauchen
        if self._subordinates_need_support(game_state):
            return self._allocate_reserves(game_state)
        
        # 4. Persönlichkeitsabhängige Entscheidung
        if situation['enemy_weakness_detected'] and self.personality.aggression > 0.6:
            return self._exploit_weakness(game_state, situation)
        
        if situation['own_forces_threatened'] and self.personality.caution > 0.6:
            return self._consolidate_position(game_state)
        
        # 5. Default: Überwache Situation
        return Decision(
            agent_id=self.id,
            action=Action.WAIT,
            target=None,
            reasoning=f"Monitoring situation. Enemy strength: {situation['enemy_strength_estimate']:.0%}",
            confidence=self.belief_state.confidence
        )
    
    def _assess_strategic_situation(self, game_state) -> dict:
        """Strategische Lagebeurteilung"""
        
        # Eigene Stärke
        own_strength = sum(
            game_state.units[uid].strength
            for uid in self._get_all_units_recursive(game_state)
        ) / max(1, len(self._get_all_units_recursive(game_state)))
        
        # Feindstärke (aus Belief State)
        enemy_positions = len(self.belief_state.enemy_strength_estimate)
        enemy_strength_estimate = sum(
            conf for conf in self.belief_state.enemy_strength_estimate.values()
        ) / max(1, enemy_positions)
        
        # Kritische Situationen
        threatened_subordinates = [
            sub for sub in self.subordinates
            if self._is_subordinate_threatened(sub, game_state)
        ]
        
        # Schwächen beim Feind
        weak_points = self._identify_enemy_weaknesses(game_state)
        
        return {
            'own_strength': own_strength,
            'enemy_strength_estimate': enemy_strength_estimate,
            'own_forces_threatened': len(threatened_subordinates) > 0,
            'threatened_subordinates': threatened_subordinates,
            'enemy_weakness_detected': len(weak_points) > 0,
            'weak_points': weak_points,
            'supply_status': self._assess_supply(),
            'morale_status': self._assess_morale(game_state)
        }
    
    def _is_objective_achieved(self, game_state) -> bool:
        """Ist aktuelles Ziel erreicht?"""
        if not self.strategic_objective:
            return True
        
        # Check victory conditions
        for condition in game_state.victory_conditions:
            if condition['type'] == 'territorial':
                target = Position(
                    condition['target']['x'],
                    condition['target']['y']
                )
                # Haben wir Einheiten dort?
                return any(
                    game_state.units[uid].position == target
                    for uid in self._get_all_units_recursive(game_state)
                )
        
        return False
    
    def _subordinates_need_support(self, game_state) -> bool:
        """Brauchen unterstellte Kommandeure Hilfe?"""
        for sub_id in self.subordinates:
            subordinate = game_state.agents[sub_id]
            
            # Check messages/reports
            # Check unit strength
            sub_units = subordinate.units_under_command
            if sub_units:
                avg_strength = sum(
                    game_state.units[uid].strength for uid in sub_units
                ) / len(sub_units)
                
                if avg_strength < 0.5:  # Kritische Verluste
                    return True
        
        return False
    
    def _allocate_reserves(self, game_state) -> Decision:
        """Verteile Reserven an bedrohte Einheiten"""
        
        # Finde kritischsten Punkt
        most_threatened = None
        lowest_strength = 1.0
        
        for sub_id in self.subordinates:
            subordinate = game_state.agents[sub_id]
            strength = self._calculate_subordinate_strength(subordinate, game_state)
            
            if strength < lowest_strength:
                lowest_strength = strength
                most_threatened = subordinate
        
        if most_threatened and self.reserve_units:
            return Decision(
                agent_id=self.id,
                action=Action.MOVE,
                target=self._get_subordinate_position(most_threatened, game_state),
                reasoning=f"Committing reserves to support {most_threatened.name} (strength: {lowest_strength:.0%})",
                confidence=0.8
            )
        
        return Decision(
            agent_id=self.id,
            action=Action.WAIT,
            target=None,
            reasoning="No reserves available",
            confidence=0.5
        )
    
    def _exploit_weakness(self, game_state, situation) -> Decision:
        """Nutze identifizierte Schwäche"""
        
        weak_point = situation['weak_points'][0] if situation['weak_points'] else None
        
        if weak_point:
            return Decision(
                agent_id=self.id,
                action=Action.ATTACK,
                target=weak_point,
                reasoning=f"Exploiting enemy weakness at {weak_point}. Aggressive personality drives offensive action.",
                confidence=0.7 + (self.personality.aggression * 0.2)
            )
        
        return self._default_decision()
    
    def _consolidate_position(self, game_state) -> Decision:
        """Festige Position"""
        return Decision(
            agent_id=self.id,
            action=Action.DEFEND,
            target=None,
            reasoning="Consolidating forces. Cautious personality prioritizes security.",
            confidence=0.6 + (self.personality.caution * 0.3)
        )
    
    def _identify_enemy_weaknesses(self, game_state) -> list:
        """Finde Schwachstellen beim Feind"""
        weaknesses = []
        
        for pos, confidence in self.belief_state.enemy_strength_estimate.items():
            if confidence < 0.4:  # Geringe vermutete Stärke
                weaknesses.append(pos)
        
        return weaknesses
    
    def _get_all_units_recursive(self, game_state) -> list:
        """Alle Einheiten unter Kommando (inkl. Untergebene)"""
        all_units = list(self.units_under_command)
        
        for sub_id in self.subordinates:
            subordinate = game_state.agents[sub_id]
            all_units.extend(subordinate.units_under_command)
            
            # Rekursiv für mehrere Ebenen
            if hasattr(subordinate, 'subordinates'):
                for subsub_id in subordinate.subordinates:
                    subsubordinate = game_state.agents[subsub_id]
                    all_units.extend(subsubordinate.units_under_command)
        
        return all_units
    
    def _is_subordinate_threatened(self, sub_id: str, game_state) -> bool:
        subordinate = game_state.agents[sub_id]
        strength = self._calculate_subordinate_strength(subordinate, game_state)
        return strength < 0.5
    
    def _calculate_subordinate_strength(self, subordinate, game_state) -> float:
        if not subordinate.units_under_command:
            return 1.0
        return sum(
            game_state.units[uid].strength
            for uid in subordinate.units_under_command
        ) / len(subordinate.units_under_command)
    
    def _get_subordinate_position(self, subordinate, game_state) -> Position:
        """Durchschnittsposition der Einheiten"""
        if not subordinate.units_under_command:
            return Position(0, 0)
        
        positions = [
            game_state.units[uid].position
            for uid in subordinate.units_under_command
        ]
        
        avg_x = sum(p.x for p in positions) // len(positions)
        avg_y = sum(p.y for p in positions) // len(positions)
        
        return Position(avg_x, avg_y)
    
    def _assess_supply(self) -> float:
        return 0.8  # Placeholder
    
    def _assess_morale(self, game_state) -> float:
        units = self._get_all_units_recursive(game_state)
        if not units:
            return 1.0
        return sum(game_state.units[uid].morale for uid in units) / len(units)
    
    def _default_decision(self) -> Decision:
        return Decision(
            agent_id=self.id,
            action=Action.WAIT,
            target=None,
            reasoning="Monitoring situation",
            confidence=0.5
        )
    
    def _set_new_objective(self, game_state) -> Decision:
        # Find next objective from victory conditions
        for condition in game_state.victory_conditions:
            if condition['type'] == 'territorial':
                target = Position(
                    condition['target']['x'],
                    condition['target']['y']
                )
                self.strategic_objective = target
                
                return Decision(
                    agent_id=self.id,
                    action=Action.MOVE,
                    target=target,
                    reasoning=f"New objective: Advance to {condition['description']}",
                    confidence=0.7
                )
        
        return self._default_decision()
    
    def process_orders(self, orders: str) -> None:
        """Strategische Ebene empfängt selten Befehle von oben"""
        self.current_orders = orders