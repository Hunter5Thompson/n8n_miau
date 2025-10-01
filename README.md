# Kriegsspiel: A Turn-Based Tactics Simulation Prototype

## 1. Executive Summary

This project is a turn-based tactics and operations game with Dec-POMDP characteristics (Fog-of-War, incomplete information, friction). The primary goal is to build a playable prototype with traceable orchestration, robust core systems, and clear interfaces. This foundation will allow for iterative development of new features, such as LLM-based agent policies, advanced tools, and an evaluator-optimizer loop.

A game turn represents 2 hours of real-time and is divided into the following phases:
1.  **Intelligence** (15m)
2.  **Planning** (45m)
3.  **Orders** (30m)
4.  **Execution** (30m)
5.  **Assessment** (variable)

Victory can be achieved through territorial control or enemy attrition.

## 2. Core Features

*   **Turn-Based Simulation:** A core game loop that processes turns, phases, and events.
*   **Hierarchical Agents:** Agents operate on three levels (Strategic, Operational, Tactical), each with distinct personalities and decision-making logic.
*   **Dynamic Scenarios:** Scenarios, maps, and force structures are loaded from simple `YAML` files.
*   **Friction of War:** The simulation models real-world complexities like weather, supply issues, and communication failures.
*   **Modular Architecture:** A layered architecture that separates concerns, making the system extensible and testable.
*   **Determinism:** The simulation is deterministic and can be reproduced by setting a `SEED` value.
*   **Evaluation & Optimization:** A built-in `Evaluator` measures performance metrics and can suggest policy tweaks for subsequent turns.

## 3. Architecture Overview

The project is built using a layered architecture to separate concerns:

-   `config/`: `YAML` files for scenarios and agent profiles.
-   `src/kriegsspiel/`: The main application package.
    -   `core/`: Core data types, game state, map, and unit definitions.
    -   `agents/`: Base agent classes and specific implementations for each command level.
    -   `decisions/`: Policy routing, decision-making logic, and action resolution.
    -   `communication/`: Messaging system, including delays and queues.
    -   `intelligence/`: Fog of War, observation, and reconnaissance logic.
    -   `combat/`: Combat resolution, including material quality and morale effects.
    -   `friction/`: Friction event generation (weather, supply, etc.).
    -   `orchestrator/`: Scenario loading, turn management, and event dispatching.
    -   `review/`: Evaluation, metrics, and After-Action Reporting (AAR).
    -   `ui/`: Text-based interface for displaying game state and results.
    -   `tools/`: Agent-usable tools for augmented decision-making (e.g., recon sweeps).

## 4. Getting Started

Follow these instructions to set up the development environment and run the simulation.

### Prerequisites

-   Python 3.8+
-   `pip` and `venv`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install the project in editable mode:**
    This command installs the project and all its dependencies (defined in `pyproject.toml`) into your virtual environment. The `-e` flag ensures that any changes you make to the source code are immediately reflected without needing to reinstall.
    ```bash
    pip install -e .
    ```

### Running Tests

To verify that the installation was successful and the core components are working, run the test suite:

```bash
python -m pytest
```

## 5. Configuration

Application settings, such as API keys for optional LLM providers, are managed via a `.env` file.

1.  **Create the `.env` file:**
    Copy the example file to create your local configuration.
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**
    Open the `.env` file and add any necessary values, such as API keys or changes to the `LOG_LEVEL`.

## 6. Running the Simulation

To start the main application, run the `main.py` script:

```bash
python main.py
```