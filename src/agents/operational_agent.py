from .base_agent import BaseAgent
from .personality import Personality
from ..core.types import Rank, Decision, Action, Position

class OperationalAgent(BaseAgent):
    """
    Operative Ebene - Korps/Divisions-Kommandeur
    
    Fokus:
    - Umsetzung strategischer Ziele
    - Koordination mehrerer Bataillone
    - Manöver auf operativer Ebene
    - Balance zwischen eigenem Ermessen und Befehlskette
    """
    
    def __init__(self, agent_id: str, name: str, personality: Personality):
        super().__init__(agent_id, name, Rank.OPERATIONAL, personality)
        self.current_mission = None
        self.requests_sent = []
        
    def decide(self, game_state) -> Decision:
        """Operative Entscheidung"""
        
        # 1. Habe ich klare Befehle?
        if not self.current_orders:
            if self.personality.should_wait_for_orders():
                return self._request_orders(game_state)
            elif self.personality.should_act_independently():
                return self._act_on_own_initiative(game_state)
        
        # 2. Lagebeurteilung
        situation = self._assess_operational_situation(game_state)
        
        # 3. Passen Befehle noch zur Lage?
        if self._orders_obsolete(situation):
            return self._report_and_request_guidance(game_state, situation)
        
        # 4. Umsetzen der Befehle
        return self._execute_orders(game_state, situation)
    
    def _assess_operational_situation(self, game_state) -> dict:
        """Operative Lagebeurteilung"""
        
        own_units = [game_state.units[uid] for uid in self.units_under_command]
        
        # Durchschnittswerte
        avg_strength = sum(u.strength for u in own_units) / max(1, len(own_units))
        avg_supply = sum(u.supply for u in own_units) / max(1, len(own_units))
        avg_morale = sum(u.morale for u in own_units) / max(1, len(own_units))
        
        # Feindkontakt
        enemy_nearby = self._count_enemy_nearby(game_state)
        
        # Gelände
        terrain_advantage = self._assess_terrain(game_state)
        
        return {
            'avg_strength': avg_strength,
            'avg_supply': avg_supply,
            'avg_morale': avg_morale,
            'enemy_nearby': enemy_nearby,
            'terrain_advantage': terrain_advantage,
            'under_pressure': enemy_nearby > len(own_units),
            'can_advance': avg_strength > 0.7 and avg_supply > 0.5
        }
    
    def _orders_obsolete(self, situation: dict) -> bool:
        """Sind Befehle noch gültig?"""
        
        # Unter starkem Druck aber Angriffsbefehl
        if situation['under_pressure'] and "advance" in self.current_orders.lower():
            return True
        
        # Schwache Einheiten aber soll weiter
        if situation['avg_strength'] < 0.4 and "attack" in self.current_orders.lower():
            return True
        
        return False
    
    def _request_orders(self, game_state) -> Decision:
        """Fordere Befehle an"""
        return Decision(
            agent_id=self.id,
            action=Action.REPORT,
            target=None,
            reasoning="Awaiting orders from higher command. High coordination personality requires clear direction.",
            confidence=0.3
        )
    
    def _act_on_own_initiative(self, game_state) -> Decision:
        """Handle ohne Befehle (Auftragstaktik!)"""
        
        situation = self._assess_operational_situation(game_state)
        
        # Schätze was der Strategic Commander will
        if situation['can_advance']:
            target = self._find_valuable_target(game_state)
            
            return Decision(
                agent_id=self.id,
                action=Action.MOVE,
                target=target,
                reasoning=f"Acting on own initiative (Initiative: {self.personality.initiative:.1f}). Advancing to exploit opportunity.",
                confidence=0.5 + (self.personality.initiative * 0.3)
            )
        
        return Decision(
            agent_id=self.id,
            action=Action.DEFEND,
            target=None,
            reasoning="No clear orders, establishing defensive position per doctrine",
            confidence=0.4
        )
    
    def _report_and_request_guidance(self, game_state, situation) -> Decision:
        """Melde Lageänderung nach oben"""
        
        report = f"Current orders unsuitable. Enemy strength: {situation['enemy_nearby']}, Own strength: {situation['avg_strength']:.0%}"
        
        return Decision(
            agent_id=self.id,
            action=Action.REPORT,
            target=None,
            reasoning=report,
            confidence=0.6
        )
    
    def _execute_orders(self, game_state, situation) -> Decision:
        """Setze Befehle um"""
        
        # Parse orders (simplified)
        if "advance" in self.current_orders.lower() or "attack" in self.current_orders.lower():
            target = self._find_attack_target(game_state)
            
            return Decision(
                agent_id=self.id,
                action=Action.ATTACK,
                target=target,
                reasoning=f"Executing orders: {self.current_orders}",
                confidence=0.7
            )
        
        elif "defend" in self.current_orders.lower() or "hold" in self.current_orders.lower():
            return Decision(
                agent_id=self.id,
                action=Action.DEFEND,
                target=None,
                reasoning=f"Executing orders: {self.current_orders}",
                confidence=0.8
            )
        
        # Default
        return Decision(
            agent_id=self.id,
            action=Action.WAIT,
            target=None,
            reasoning="Orders unclear, awaiting clarification",
            confidence=0.4
        )
    
    def _count_enemy_nearby(self, game_state) -> int:
        """Feinde in Nähe"""
        count = 0
        
        own_positions = [
            game_state.units[uid].position
            for uid in self.units_under_command
        ]
        
        for pos, confidence in self.belief_state.enemy_strength_estimate.items():
            if confidence > 0.5:  # Nur sichere Sichtungen
                for own_pos in own_positions:
                    if pos.distance_to(own_pos) <= 3:
                        count += 1
                        break
        
        return count
    
    def _assess_terrain(self, game_state) -> float:
        """Geländevorteil"""
        # Simplified
        return 0.5
    
    def _find_valuable_target(self, game_state) -> Position:
        """Finde wertvolles Ziel"""
        # Finde nächste Stadt
        for pos, terrain in game_state.terrain.items():
            if terrain == 'town':
                return pos
        
        # Fallback: Vorwärts
        own_pos = game_state.units[self.units_under_command[0]].position
        return Position(own_pos.x + 2, own_pos.y)
    
    def _find_attack_target(self, game_state) -> Position:
        """Finde Angriffsziel"""
        # Schwächster bekannter Feind
        weakest_pos = None
        weakest_conf = 1.0
        
        for pos, conf in self.belief_state.enemy_strength_estimate.items():
            if conf < weakest_conf:
                weakest_conf = conf
                weakest_pos = pos
        
        return weakest_pos if weakest_pos else self._find_valuable_target(game_state)
    
    def process_orders(self, orders: str) -> None:
        """Empfange Befehle von oben"""
        self.current_orders = orders