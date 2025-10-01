#!/usr/bin/env python3
"""Kriegsspiel - Dec-POMDP Tactical War Game"""

import logging
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """Allow running the app via ``python main.py`` without installation."""

    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    src_str = str(src_dir)
    if src_dir.exists() and src_str not in sys.path:
        sys.path.insert(0, src_str)


_ensure_src_on_path()

from kriegsspiel.orchestrator.scenario_loader import ScenarioLoader
from kriegsspiel.orchestrator.turn_manager import TurnManager
from kriegsspiel.review.aar_agent import AARAgent
from kriegsspiel.ui.text_interface import TextInterface

def setup_logging():
    """Configures basic logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # filename='kriegsspiel.log', # Uncomment to log to a file
        # filemode='w'
    )

def main():
    """Hauptfunktion zum Initialisieren und Ausführen der Spielsimulation."""
    setup_logging()
    print("="*60)
    print("KRIEGSSPIEL - Dec-POMDP Prototype")
    print("="*60)
    
    # Szenario laden
    game_state = ScenarioLoader.load("config/scenarios/operation_herbststurm.yaml")
    
    if not game_state:
        logging.error("Fehler: Das Szenario konnte nicht geladen werden. Programm wird beendet.")
        return

    # Initialisierung der Systemkomponenten
    turn_manager = TurnManager(game_state)
    aar_agent = AARAgent()
    ui = TextInterface()
    
    logging.info(f"Szenario '{game_state.scenario_name}' geladen. Starte Simulation...")
    
    # Vollständige Spielschleife (Game Loop)
    while not game_state.is_finished():
        ui.display_turn_header(game_state)
        ui.display_map(game_state)
        
        # Eine Spielrunde ausführen
        turn_results = turn_manager.execute_turn()
        
        # Ergebnisse der Runde anzeigen
        ui.display_results(turn_results)
        
        # Daten für den After-Action Report sammeln
        # Extract metrics from the turn result to pass to the AAR agent
        metrics = turn_results.phase_details.get('assessment', {}).get('metrics', {})
        aar_agent.record_turn(game_state.turn -1, turn_results, metrics) # turn is already incremented
        
        # Siegbedingungen prüfen, um die Schleife ggf. vorzeitig zu beenden
        if game_state.check_victory():
            logging.info("Victory condition met. Ending simulation.")
            break
            
    # Spielende und finaler Bericht
    print("\n" + "="*60)
    print("Simulation beendet.")

    if game_state.check_victory():
        print("Ergebnis: Sieg!")
    else:
        print("Ergebnis: Rundenlimit erreicht.")

    print("="*60)
    
    # Finalen After-Action Report erstellen und ausgeben
    final_report = aar_agent.generate_final_report(game_state)
    print(final_report)

if __name__ == "__main__":
    main()
