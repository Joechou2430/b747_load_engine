# B747-400F Intelligent Load Planning Engine

An intelligent load simulation engine designed specifically for the B747-400F freighter, aimed at assisting Revenue Management Systems (RMS) and sales teams in accurate space estimation and pricing.

## Core Features

1. **Shoring Logic (Dunnage & Pallet Type Recommendations)**

   *Automatically detects overweight cargo (triggering 16ft/20ft pallet requirements).

   *Calculates required shoring height and dead weight for legal overhangs in lower deck compartments.

2. **Interlock System**

   *Supports 20ft longitudinal interlocking in the main deck (occupying adjacent rows).

   *Supports mutual exclusivity logic between Center PMC and Side Containers in the lower deck.

3. **Optimization**

   *Integrates Google OR-Tools (SCIP Solver).

   *Optimizes 3D Bin Packing for loose cargo (minimizing mixed-loading).

4. **Constraints (Structural Limits)**

   *Fuselage linear load limits.

   *IATA DGR (Dangerous Goods Regulations) segregation checks.

## Project Structure

- `app/config.py`:Coordinates, Limits
- `app/logic/`: Shoring, Segregation, Structural Checks
- `app/planner/`: Mathematical Solver, Heuristic Allocation
- `app/api.py`: Simulate & Booking

## Installation & Execution

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Tests (CLI Mode)**
    ```bash
    python main.py
    ```

3.  **un Web Interface (Testing UI)**
    ```bash
    python app.py
    ```
    Visit `http://127.0.0.1:5000`

## Tech Stack

- **Language**: Python 3.9+
- **Solver**: Google OR-Tools (MIP)
- **Web Framework**: Flask (For testing UI)