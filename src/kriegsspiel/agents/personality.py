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
    """Lädt Persönlichkeiten aus YAML und cached sie für wiederholte Zugriffe."""

    _profile_cache: Dict[str, Personality] = {}
    _cache_path: str = ""

    @classmethod
    def load_profiles(cls, config_path: str = "config/personality_profiles.yaml") -> Dict[str, Personality]:
        if not cls._profile_cache or cls._cache_path != config_path:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)

            cls._profile_cache = {
                name: Personality(
                    aggression=profile['aggression'],
                    caution=profile['caution'],
                    initiative=profile['initiative'],
                    coordination=profile['coordination'],
                    description=profile['description'],
                    decision_modifiers=profile.get('decision_modifiers', {})
                )
                for name, profile in data.get('profiles', {}).items()
            }
            cls._cache_path = config_path

        return cls._profile_cache

    @classmethod
    def get_profile(cls, name: str, config_path: str = "config/personality_profiles.yaml") -> Personality:
        profiles = cls.load_profiles(config_path)
        if name in profiles:
            return profiles[name]
        # Fallback: balanced Profil oder erstes verfügbares Profil
        if 'balanced' in profiles:
            return profiles['balanced']
        return next(iter(profiles.values())) if profiles else Personality(0.5, 0.5, 0.5, 0.5)
