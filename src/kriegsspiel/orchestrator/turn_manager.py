from typing import List, Dict
from dataclasses import dataclass
from kriegsspiel.core.game_state import GameState
from kriegsspiel.core.types import Rank, Decision, TurnResult
from kriegsspiel.agents.base_agent import BaseAgent
from kriegsspiel.communication.message import MessageQueue
from kriegsspiel.friction.friction_generator import FrictionGenerator
from kriegsspiel.combat.combat_resolver import CombatResolver
from kriegsspiel.intelligence.observation_generator import ObservationGenerator
from kriegsspiel.review.evaluator import Evaluator

class TurnManager:
    """
    Orchestriert einen kompletten Turn
    
    Ein Turn = 2 Stunden Spielzeit
    Phasen: Intelligence -> Planning -> Orders -> Execution -> Assessment
    """
    
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.message_queue = MessageQueue()
        self.friction_gen = FrictionGenerator()
        self.combat_resolver = CombatResolver()
        self.observation_gen = ObservationGenerator()
        self.evaluator = Evaluator()
        
    def execute_turn(self) -> TurnResult:
        """Führt einen kompletten Turn aus"""
        
        result = TurnResult(
            turn_number=self.game_state.turn,
            decisions=[],
            combat_results=[],
            friction_events=[],
            messages_delivered=[],
            phase_details={}
        )
        
        # Phase 1: Intelligence
        intelligence = self._intelligence_phase()
        result.phase_details['intelligence'] = intelligence
        
        # Phase 2: Planning (Agents entscheiden)
        decisions = self._planning_phase()
        result.decisions = decisions
        
        # Phase 3: Orders (Befehle mit Delay)
        messages = self._orders_phase(decisions)
        result.messages_delivered = messages
        
        # Phase 4: Execution (Bewegung, Kampf)
        execution = self._execution_phase(decisions)
        result.combat_results = execution['combat']
        result.phase_details['execution'] = execution
        
        # Phase 5: Assessment (Friction, Updates, Evaluation)
        assessment = self._assessment_phase()
        result.friction_events = assessment['friction']

        # Evaluate the turn's outcome
        metrics = self.evaluator.evaluate(self.game_state, result)
        assessment['metrics'] = metrics
        result.phase_details['assessment'] = assessment
        
        # Turn abschließen
        self.game_state.turn += 1
        
        return result
    
    def _intelligence_phase(self) -> Dict:
        """
        Phase 1: Aufklärung und Beobachtungen
        
        Jeder Agent erhält neue Observationen basierend auf:
        - Einheiten unter Kommando
        - Aufklärungseinheiten
        - Berichte von Untergebenen
        - Zeitverzögerung
        """
        observations = {}
        
        for agent_id, agent in self.game_state.agents.items():
            # Generiere Beobachtungen für diesen Agent
            obs = self.observation_gen.generate_observation(
                agent=agent,
                game_state=self.game_state,
                visibility_range=self._get_visibility_range(agent)
            )
            
            # Update Agent's Belief State
            agent.belief_state.update(obs)
            observations[agent_id] = obs
        
        return {
            'observations': observations,
            'recon_conducted': self._count_recon_units()
        }
    
    def _planning_phase(self) -> List[Decision]:
        """
        Phase 2: Agenten treffen Entscheidungen
        
        Hierarchisch: Strategic -> Operational -> Tactical
        Obere Ebenen entscheiden zuerst, untere reagieren darauf
        """
        decisions = []
        
        # Reihenfolge wichtig!
        for rank in [Rank.STRATEGIC, Rank.OPERATIONAL, Rank.TACTICAL]:
            agents = self._get_agents_by_rank(rank)
            
            for agent in agents:
                # Agent trifft Entscheidung basierend auf:
                # - Eigenem Belief State
                # - Befehlen von oben (falls vorhanden)
                # - Persönlichkeit
                decision = agent.decide(self.game_state)
                decisions.append(decision)
                
                # Log für AAR
                self.game_state.log_event(
                    f"{agent.name} ({rank.value}): {decision.action.value} - {decision.reasoning}"
                )
        
        return decisions
    
    def _orders_phase(self, decisions: List[Decision]) -> List:
        """
        Phase 3: Befehle werden übermittelt
        
        KRITISCH: Kommunikation braucht Zeit!
        - Strategic -> Operational: 1 Turn
        - Operational -> Tactical: 1 Turn
        - Urgent messages: -1 Turn
        """
        messages_delivered = []
        
        # Bestehende Messages ausliefern
        deliverable = self.message_queue.get_deliverable(self.game_state.turn)
        for msg in deliverable:
            receiver = self.game_state.agents[msg.receiver]
            receiver.process_orders(msg.content)
            messages_delivered.append(msg)
            
            self.game_state.log_event(
                f"Message delivered: {msg.sender} -> {msg.receiver} (sent T{msg.turn_sent})"
            )
        
        # Neue Messages aus Decisions erstellen
        for decision in decisions:
            if decision.action.value == "report":
                # Meldung nach oben
                agent = self.game_state.agents[decision.agent_id]
                if agent.superior:
                    msg = self._create_message(
                        sender=agent.id,
                        receiver=agent.superior,
                        content=decision.reasoning,
                        current_turn=self.game_state.turn
                    )
                    self.message_queue.add(msg)
        
        return messages_delivered
    
    def _execution_phase(self, decisions: List[Decision]) -> Dict:
        """
        Phase 4: Aktionen werden ausgeführt
        
        - Bewegung
        - Kampf
        - Aufklärung
        
        Simultane Ausführung mit Interaktionen
        """
        combat_results = []
        movements = []
        
        # Gruppiere nach Action-Type
        actions_by_type = self._group_decisions_by_action(decisions)
        
        # 1. Bewegungen zuerst
        for decision in actions_by_type.get('move', []):
            moved = self._execute_movement(decision)
            movements.append(moved)
        
        # 2. Dann Kämpfe
        for decision in actions_by_type.get('attack', []):
            combat = self._execute_combat(decision)
            if combat:
                combat_results.append(combat)
        
        # 3. Aufklärung
        for decision in actions_by_type.get('recon', []):
            self._execute_recon(decision)
        
        return {
            'combat': combat_results,
            'movements': movements
        }
    
    def _assessment_phase(self) -> Dict:
        """
        Phase 5: Zustandsupdate und Friction
        
        - Friction Events generieren
        - Versorgung aktualisieren
        - Moral checken
        - Verluste verarbeiten
        """
        friction_events = []
        
        # Friction generieren
        friction = self.friction_gen.generate(self.game_state)
        if friction:
            friction_events.append(friction)
            self._apply_friction(friction)
            
            self.game_state.log_event(
                f"[FRICTION] {friction.description}"
            )
        
        # Supply Update
        self._update_supply()
        
        # Morale Check
        self._check_morale()
        
        return {
            'friction': friction_events,
            'supply_status': self._get_supply_status(),
            'morale_status': self._get_morale_status()
        }
    
    def _execute_movement(self, decision: Decision) -> Dict:
        """Führt Bewegung aus"""
        agent = self.game_state.agents[decision.agent_id]
        
        for unit_id in agent.units_under_command:
            unit = self.game_state.units[unit_id]
            
            if decision.target:
                # Berechne Bewegungskosten
                distance = unit.position.distance_to(decision.target)
                terrain_cost = self._get_movement_cost(unit.position, decision.target)
                
                # Kann Einheit das erreichen?
                max_move = self._get_max_movement(unit)
                
                if distance * terrain_cost <= max_move:
                    old_pos = unit.position
                    unit.position = decision.target
                    
                    return {
                        'unit': unit_id,
                        'from': old_pos,
                        'to': decision.target,
                        'success': True
                    }
        
        return {'success': False}
    
    def _execute_combat(self, decision: Decision) -> Dict:
        """Führt Kampf aus"""
        agent = self.game_state.agents[decision.agent_id]
        
        # Finde Angreifer-Einheiten
        attackers = [
            self.game_state.units[uid]
            for uid in agent.units_under_command
        ]
        
        # Finde Verteidiger bei Zielposition
        defenders = [
            unit for unit in self.game_state.units.values()
            if unit.position == decision.target
            and unit.commander not in self.game_state.get_friendly_agents(agent.id)
        ]
        
        if not defenders:
            return None
        
        # Kampf für jede Angreifer/Verteidiger-Paarung
        results = []
        for attacker in attackers:
            for defender in defenders:
                # Wurde Angreifer entdeckt?
                attacker_detected = self._is_unit_detected(
                    attacker, defender.commander
                )
                defender_detected = self._is_unit_detected(
                    defender, attacker.commander
                )
                
                result = self.combat_resolver.resolve_combat(
                    attacker=attacker,
                    defender=defender,
                    terrain=self.game_state.terrain,
                    attacker_detected=attacker_detected,
                    defender_detected=defender_detected
                )
                
                # Wende Verluste an
                attacker.strength = max(0.0, min(1.0, attacker.strength - result.attacker_losses))
                defender.strength = max(0.0, min(1.0, defender.strength - result.defender_losses))
                attacker.morale = max(0.0, min(1.0, attacker.morale + result.attacker_morale_impact))
                defender.morale = max(0.0, min(1.0, defender.morale + result.defender_morale_impact))
                
                results.append({
                    'attacker': attacker.id,
                    'defender': defender.id,
                    'result': result
                })
                
                self.game_state.log_event(result.description)
        
        return results
    
    def _execute_recon(self, decision: Decision):
        """Führt Aufklärung aus"""
        # Verbessert Belief State für diesen Agent
        agent = self.game_state.agents[decision.agent_id]
        
        # Generiere bessere Observation im Zielgebiet
        enhanced_obs = self.observation_gen.generate_recon_observation(
            position=decision.target,
            game_state=self.game_state,
            quality=0.9  # Hohe Qualität durch dedizierte Aufklärung
        )
        
        agent.belief_state.update(enhanced_obs)
    
    # Helper Methods
    
    def _get_visibility_range(self, agent: BaseAgent) -> int:
        """Sichtweite basierend auf Rang und Einheiten"""
        base_range = {
            Rank.STRATEGIC: 5,
            Rank.OPERATIONAL: 3,
            Rank.TACTICAL: 2
        }[agent.rank]
        
        # Aufklärungseinheiten erhöhen Reichweite
        recon_units = sum(
            1 for uid in agent.units_under_command
            if self.game_state.units[uid].type.value == 'recon'
        )
        
        return base_range + recon_units
    
    def _get_agents_by_rank(self, rank: Rank) -> List[BaseAgent]:
        return [
            agent for agent in self.game_state.agents.values()
            if agent.rank == rank
        ]
    
    def _group_decisions_by_action(self, decisions: List[Decision]) -> Dict:
        grouped = {}
        for decision in decisions:
            action = decision.action.value
            if action not in grouped:
                grouped[action] = []
            grouped[action].append(decision)
        return grouped
    
    # src/orchestrator/turn_manager.py
    def _create_message(self, sender: str, receiver: str, content: str, current_turn: int):
        from kriegsspiel.communication.message import Message
        from kriegsspiel.core.types import Rank
        
        sender_agent = self.game_state.agents[sender]
        receiver_agent = self.game_state.agents[receiver]
        
        # Delay-Berechnung direkt hier
        hierarchy = [Rank.TACTICAL, Rank.OPERATIONAL, Rank.STRATEGIC]
        sender_idx = hierarchy.index(sender_agent.rank)
        receiver_idx = hierarchy.index(receiver_agent.rank)
        
        if sender_idx < receiver_idx:  # upward
            base_delay = 1
        elif sender_idx > receiver_idx:  # downward
            base_delay = 2
        else:  # same level
            base_delay = 2
        
        return Message(
            sender=sender,
            receiver=receiver,
            content=content,
            turn_sent=current_turn,
            turn_received=current_turn + base_delay,
            priority=1
        )
    
    def _apply_friction(self, friction_event):
        """Wendet Friction-Effekte an"""
        for effect, value in friction_event.effects.items():
            if effect == "communication_delay":
                # Verzögere alle pending messages
                for msg in self.message_queue.queue:
                    msg.turn_received += value
            
            elif effect == "movement_modifier":
                # Reduziere Bewegungsreichweite aller Einheiten
                for unit in self.game_state.units.values():
                    unit.movement_modifier = value
    
    def _update_supply(self):
        for unit in self.game_state.units.values():
            if not self._is_supplied(unit):
                unit.supply = max(0.0, unit.supply - 0.1)
    
    def _check_morale(self):
        for unit in self.game_state.units.values():
            if unit.supply < 0.3:
                unit.morale = max(0.0, unit.morale - 0.05)
            if unit.strength < 0.4:
                unit.morale = max(0.0, unit.morale - 0.1)
    
    def _is_unit_detected(self, unit, enemy_commander_id: str) -> bool:
        """Wurde Einheit vom Feind entdeckt?"""
        enemy_agent = self.game_state.agents[enemy_commander_id]
        
        # Check ob Position in enemy belief state
        for pos, confidence in enemy_agent.belief_state.enemy_strength_estimate.items():
            if pos == unit.position and confidence > 0.5:
                return True
        
        return False
    
    def _get_movement_cost(self, from_pos, to_pos) -> float:
        terrain = self.game_state.terrain.get(to_pos, 'open')
        costs = {
            'open': 1.0,
            'forest': 1.5,
            'hill': 1.3,
            'road': 0.5,
            'town': 1.0
        }
        return costs.get(terrain, 1.0)
    
    def _get_max_movement(self, unit) -> float:
        base = {
            'infantry': 2,
            'armor': 4,
            'recon': 6
        }[unit.type.value]
        
        # Modifikatoren
        modifier = getattr(unit, 'movement_modifier', 1.0)
        supply_factor = max(0.5, unit.supply)
        
        return base * modifier * supply_factor
    
    def _is_supplied(self, unit) -> bool:
        # Simplified: Check Distanz zu friendly town
        friendly_towns = [
            pos for pos, terrain in self.game_state.terrain.items()
            if terrain == 'town' and self._is_friendly_controlled(pos, unit.commander)
        ]
        
        if not friendly_towns:
            return False
        
        min_dist = min(unit.position.distance_to(town) for town in friendly_towns)
        return min_dist <= 5  # Supply range
    
    def _count_recon_units(self) -> int:
        return sum(1 for u in self.game_state.units.values() if u.type.value == 'recon')
    
    def _get_supply_status(self) -> Dict:
        return {
            'average': sum(u.supply for u in self.game_state.units.values()) / len(self.game_state.units)
        }
    
    def _get_morale_status(self) -> Dict:
        return {
            'average': sum(u.morale for u in self.game_state.units.values()) / len(self.game_state.units)
        }
    
    def _is_friendly_controlled(self, pos, commander_id) -> bool:
        # Simplified
        return True