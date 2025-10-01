from .base_agent import BaseAgent
from .personality import Personality
from ..core.types import Rank, Decision, Action, Position

class TacticalAgent(BaseAgent):
    """
    Taktische Ebene - Bataillons/Kompanie-Kommandeur
    
    Fokus:
    - Direkte Gefechtsfeldführung
    - Unmittelbarer Feindkontakt
    - Schnelle Entscheidungen
    - Spannung zwischen Befehlen und Realität
    """
    
    def __init__(self, agent_id: str, name: str, personality: Personality):
        super().__init__(agent_id, name, Rank.TACTICAL, personality)
        self.last_contact_turn = 0
        self.under_fire = False
        
    def decide(self, game_state) -> Decision:
        """Taktische Entscheidung - oft unter Zeitdruck"""
        
        # 1. Unmittelbare Gefahr?
        immediate_threat = self._check_immediate_threat(game_state)
        
        if immediate_threat:
            self.under_fire = True
            return self._react_to_threat(game_state, immediate_threat)
        
        # 2. Habe ich aktuelle Befehle?
        if not self.current_orders:
            return self._act_without_orders(game_state)
        
        # 3. Befehle vs. Realität
        situation = self._assess_tactical_situation(game_state)
        
        # Befehle sagen "vorwärts", aber starker Feind
        if self._orders_conflict_with_reality(situation):
            return self._handle_conflict(game_state, situation)
        
        # 4. Führe Befehle aus
        return self._execute_tactical_orders(game_state, situation)
    
    def _check_immediate_threat(self, game_state) -> dict:
        """Unmittelbare Bedrohung auf dem Gefechtsfeld"""
        
        own_units = [game_state.units[uid] for uid in self.units_under_command]
        
        threats = []
        for own_unit in own_units:
            for enemy_pos, confidence in self.belief_state.enemy_strength_estimate.items():
                distance = own_unit.position.distance_to(enemy_pos)
                
                if distance <= 2 and confidence > 0.6:  # Direkte Bedrohung
                    threats.append({
                        'position': enemy_pos,
                        'distance': distance,
                        'confidence': confidence
                    })
        
        return threats[0] if threats else None
    
    def _react_to_threat(self, game_state, threat: dict) -> Decision:
        """Reagiere auf unmittelbare Bedrohung"""
        
        situation_factors = {
            'under_fire': 1.0,
            'casualties': self._calculate_casualties(game_state)
        }
        
        risk_tolerance = self.personality.calculate_risk_tolerance(situation_factors)
        
        # Aggressive Persönlichkeit: Gegenangriff
        if risk_tolerance > 0.3:
            return Decision(
                agent_id=self.id,
                action=Action.ATTACK,
                target=threat['position'],
                reasoning=f"Under fire! Aggressive personality drives counterattack. Risk tolerance: {risk_tolerance:.2f}",
                confidence=0.6 + (self.personality.aggression * 0.3)
            )
        
        # Vorsichtige Persönlichkeit: Rückzug
        elif risk_tolerance < -0.2:
            return Decision(
                agent_id=self.id,
                action=Action.MOVE,
                target=self._find_fallback_position(game_state),
                reasoning=f"Under fire! Cautious personality directs tactical withdrawal. Risk tolerance: {risk_tolerance:.2f}",
                confidence=0.7
            )
        
        # Halten und verteidigen
        return Decision(
            agent_id=self.id,
            action=Action.DEFEND,
            target=None,
            reasoning="Under fire! Establishing defensive position.",
            confidence=0.6
        )
    
    def _act_without_orders(self, game_state) -> Decision:
        """Keine Befehle - was tun?"""
        
        # Hohe Initiative: Handle selbst
        if self.personality.initiative > 0.7:
            return Decision(
                agent_id=self.id,
                action=Action.RECON,
                target=self._find_recon_target(game_state),
                reasoning=f"No orders, high initiative ({self.personality.initiative:.1f}) drives independent recon",
                confidence=0.5
            )
        
        # Niedrige Initiative: Melde und warte
        elif self.personality.coordination > 0.7:
            return Decision(
                agent_id=self.id,
                action=Action.REPORT,
                target=None,
                reasoning="No orders received. Requesting guidance (high coordination need)",
                confidence=0.3
            )
        
        # Default: Sichere Position
        return Decision(
            agent_id=self.id,
            action=Action.DEFEND,
            target=None,
            reasoning="No orders, establishing security",
            confidence=0.4
        )
    
    def _assess_tactical_situation(self, game_state) -> dict:
        """Taktische Lage"""
        
        own_units = [game_state.units[uid] for uid in self.units_under_command]
        
        # Kampfkraft
        combat_effective = sum(1 for u in own_units if u.is_combat_effective())
        
        # Feinde sichtbar
        visible_enemies = len([
            pos for pos, conf in self.belief_state.enemy_strength_estimate.items()
            if conf > 0.5
        ])
        
        return {
            'unit_count': len(own_units),
            'combat_effective': combat_effective,
            'visible_enemies': visible_enemies,
            'outnumbered': visible_enemies > len(own_units),
            'casualties_taken': self._calculate_casualties(game_state),
            'supply_critical': any(u.supply < 0.3 for u in own_units)
        }
    
    def _orders_conflict_with_reality(self, situation: dict) -> bool:
        """Widersprechen Befehle der Realität?"""
        # Angriffsbefehle aber outnumbered
        if "attack" in self.current_orders.lower() and situation['outnumbered']:
            return True
        
        # Vorstoß befohlen aber hohe Verluste
        if "advance" in self.current_orders.lower() and situation['casualties_taken'] > 0.3:
            return True
        
        # Halten befohlen aber Position unhaltbar
        if "hold" in self.current_orders.lower() and situation['visible_enemies'] > situation['combat_effective'] * 2:
            return True
        
        return False
    
    def _handle_conflict(self, game_state, situation: dict) -> Decision:
        """Befehle widersprechen Lage - Dilemma!"""
        
        # Persönlichkeit entscheidet
        
        # Hohe Disziplin/Koordination: Befehle befolgen trotz Zweifel
        if self.personality.coordination > 0.7:
            return Decision(
                agent_id=self.id,
                action=self._parse_order_action(),
                target=None,
                reasoning=f"Orders conflict with situation but high coordination ({self.personality.coordination:.1f}) demands obedience. Following orders.",
                confidence=0.4
            )
        
        # Hohe Initiative: Eigenständig handeln
        if self.personality.initiative > 0.7:
            return Decision(
                agent_id=self.id,
                action=Action.DEFEND,
                target=None,
                reasoning=f"Orders unsuitable for current situation. High initiative ({self.personality.initiative:.1f}) drives independent decision.",
                confidence=0.6
            )
        
        # Mittelweg: Melden und um Klärung bitten
        return Decision(
            agent_id=self.id,
            action=Action.REPORT,
            target=None,
            reasoning=f"Orders conflict with reality. Enemies: {situation['visible_enemies']}, Own effective: {situation['combat_effective']}. Requesting clarification.",
            confidence=0.5
        )
    
    def _execute_tactical_orders(self, game_state, situation: dict) -> Decision:
        """Führe taktische Befehle aus"""
        
        action = self._parse_order_action()
        target = self._find_tactical_target(game_state, action)
        
        confidence = 0.7
        
        # Confidence basierend auf Situation
        if situation['outnumbered']:
            confidence -= 0.2
        if situation['supply_critical']:
            confidence -= 0.1
        
        return Decision(
            agent_id=self.id,
            action=action,
            target=target,
            reasoning=f"Executing orders: {self.current_orders}",
            confidence=max(0.3, confidence)
        )
    
    def _calculate_casualties(self, game_state) -> float:
        """Wie viele Verluste?"""
        own_units = [game_state.units[uid] for uid in self.units_under_command]
        
        if not own_units:
            return 0.0
        
        avg_strength = sum(u.strength for u in own_units) / len(own_units)
        return 1.0 - avg_strength
    
    def _find_fallback_position(self, game_state) -> Position:
        """Finde Rückzugsposition"""
        # Einfach: Zurück
        own_unit = game_state.units[self.units_under_command[0]]
        return Position(own_unit.position.x - 1, own_unit.position.y)
    
    def _find_recon_target(self, game_state) -> Position:
        """Finde Aufklärungsziel"""
        # Vorwärts scouten
        own_unit = game_state.units[self.units_under_command[0]]
        return Position(own_unit.position.x + 2, own_unit.position.y)
    
    def _parse_order_action(self) -> Action:
        """Parse Befehl zu Action"""
        orders_lower = self.current_orders.lower()
        
        if "attack" in orders_lower:
            return Action.ATTACK
        elif "advance" in orders_lower or "move" in orders_lower:
            return Action.MOVE
        elif "defend" in orders_lower or "hold" in orders_lower:
            return Action.DEFEND
        elif "recon" in orders_lower or "scout" in orders_lower:
            return Action.RECON
        
        return Action.WAIT
    
    def _find_tactical_target(self, game_state, action: Action) -> Position:
        """Finde Ziel für Action"""
        
        if action == Action.ATTACK:
            # Nächster Feind
            own_pos = game_state.units[self.units_under_command[0]].position
            
            closest_enemy = None
            min_dist = 999
            
            for enemy_pos in self.belief_state.enemy_strength_estimate.keys():
                dist = own_pos.distance_to(enemy_pos)
                if dist < min_dist:
                    min_dist = dist
                    closest_enemy = enemy_pos
            
            return closest_enemy if closest_enemy else Position(own_pos.x + 1, own_pos.y)
        
        elif action == Action.MOVE or action == Action.RECON:
            # Vorwärts
            own_pos = game_state.units[self.units_under_command[0]].position
            return Position(own_pos.x + 2, own_pos.y)
        
        return None
    
    def process_orders(self, orders: str) -> None:
        """Empfange Befehle - kritischste Ebene für Delays"""
        self.current_orders = orders
        
        # Tactical level merkt Delays am meisten
        # (Befehle von vor 2 Stunden können schon veraltet sein)