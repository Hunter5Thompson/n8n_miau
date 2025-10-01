from dataclasses import dataclass
from typing import Dict
import yaml

@dataclass
class Personality:
    aggression: float
    caution: float
    initiative: float
    coordination: float
    description: str = ""
    decision_modifiers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.decision_modifiers is None:
            self.decision_modifiers = {}
    
    def get_decision_modifier(self, situation: str) -> float:
        """Gibt situationsabhängigen Modifier"""
        return self.decision_modifiers.get(situation, 0.0)
    
    def should_act_independently(self) -> bool:
        """Sollte Agent eigenständig handeln?"""
        return self.initiative > 0.7 and self.coordination < 0.5
    
    def should_wait_for_orders(self) -> bool:
        """Sollte Agent auf Befehle warten?"""
        return self.caution > 0.7 or self.coordination > 0.7
    
    def calculate_risk_tolerance(self, situation_factors: Dict) -> float:
        """Risikobereitschaft in aktueller Situation"""
        base = self.aggression - self.caution
        
        # Situationsmodifikatoren
        for factor, value in situation_factors.items():
            base += self.get_decision_modifier(factor) * value
        
        return max(-1.0, min(1.0, base))

class PersonalityLoader:
    """Lädt Persönlichkeiten aus YAML"""
    
    @staticmethod
    def load_profiles(config_path: str = "config/personality_profiles.yaml") -> Dict:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        profiles = {}
        
        for name, profile_data in data['profiles'].items():
            profiles[name] = Personality(
                aggression=profile_data['aggression'],
                caution=profile_data['caution'],
                initiative=profile_data['initiative'],
                coordination=profile_data['coordination'],
                description=profile_data['description'],
                decision_modifiers=profile_data.get('decision_modifiers', {})
            )
        
        return profiles
    
    @staticmethod
    def get_profile(name: str) -> Personality:
        profiles = PersonalityLoader.load_profiles()
        return profiles.get(name, profiles['balanced'])