# Baduk (Go) Game Engine

This project is a Python-based implementation of the game of Baduk (also known as Go). It currently features a robust game engine with a text-based user interface (TUI) for playing.

## Features Implemented

*   **Game Board:** Configurable board size (defaults to 19x19).
*   **Stone Placement:** Supports placing Black and White stones.
*   **Capture Logic:** Correctly handles the capture of opponent stones when their group runs out of liberties.
*   **Ko Rule:** Implements a simple Ko rule, preventing immediate recapture that would revert to the exact previous board state.
*   **Passing:** Allows players to pass their turn.
*   **Game End:** The game ends when both players pass consecutively.
*   **Area Scoring:** Calculates scores at the end of the game using Area scoring rules:
    *   Counts all stones of a player's color on the board.
    *   Counts empty intersections exclusively surrounded by a single player's stones.
    *   Includes Komi (default 6.5 points for White).
*   **Text-Based User Interface (TUI):**
    *   Located in `tui.py`.
    *   Allows users to play a full game by entering coordinates (e.g., "3,4") or "pass".
    *   Displays the board, current player, captures, Ko restrictions, and final scores.
*   **Unit Tests:** A suite of unit tests (`tests/`) helps ensure the correctness of the core game logic.

## How to Run

1.  Ensure you have Python 3 installed.
2.  Clone this repository (or ensure `game.py`, `board.py`, `stone.py`, and `tui.py` are in the same directory).
3.  Navigate to the directory in your terminal.
4.  Run the Text-Based User Interface using:
    ```bash
    python tui.py
    ```
5.  You will be prompted to choose a board size (or use the default 19x19). Follow the on-screen instructions to play.

## Future Development

The project is planned to be extended with:

*   An AI opponent with configurable difficulty levels.
*   A web-based user interface for playing in a browser.