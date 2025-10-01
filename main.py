#!/usr/bin/env python3
"""
Kriegsspiel - Dec-POMDP Tactical War Game
"""

# Annahme: Die Pfade zu den Modulen sind korrekt und im PYTHONPATH
from src.orchestrator.scenario_loader import ScenarioLoader
from src.orchestrator.turn_manager import TurnManager
from src.review.aar_agent import AARAgent
from src.ui.text_interface import TextInterface

def main():
    """
    Hauptfunktion zum Initialisieren und Ausführen der Spielsimulation.
    """
    print("="*60)
    print("KRIEGSSPIEL - Dec-POMDP Prototype")
    print("="*60)
    
    # KORRIGIERT: Szenario laden
    # Der ScenarioLoader gibt direkt ein konfiguriertes GameState-Objekt zurück.
    # Der fehlerhafte Zwischenschritt über 'GameState.from_scenario' wurde entfernt.
    game_state = ScenarioLoader.load("config/scenarios/operation_herbststurm.yaml")
    
    if not game_state:
        print("Fehler: Das Szenario konnte nicht geladen werden. Programm wird beendet.")
        return

    # Initialisierung der Systemkomponenten
    turn_manager = TurnManager(game_state)
    aar_agent = AARAgent()
    ui = TextInterface()
    
    print(f"\nSzenario '{game_state.scenario_name}' geladen. Starte Simulation...")
    
    # Vollständige Spielschleife (Game Loop)
    while not game_state.is_finished():
        ui.display_turn_header(game_state)
        
        # Eine Spielrunde ausführen
        turn_results = turn_manager.execute_turn()
        
        # Ergebnisse der Runde anzeigen
        ui.display_results(turn_results)
        
        # Daten für den After-Action Report sammeln
        aar_agent.record_turn(game_state, turn_results)
        
        # Siegbedingungen prüfen, um die Schleife ggf. vorzeitig zu beenden
        if game_state.check_victory():
            break
            
    # Spielende und finaler Bericht
    print("\n" + "="*60)
    print("Simulation beendet.")
    winner = game_state.get_winner()
    if winner:
        print(f"Sieger: {winner.upper()}")
    else:
        print("Ergebnis: Unentschieden oder Rundenlimit erreicht.")
    print("="*60)
    
    # Finalen After-Action Report erstellen
    aar_agent.generate_final_report()

if __name__ == "__main__":
    main()