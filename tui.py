
from game import Game, Stone
import time # For AI vs AI delay

def print_game_state(game_instance):
    print("\n" + "="*20)
    print(game_instance.get_board_display_string())
    current_scores = game_instance.get_scores()
    if not game_instance.game_over:
        print(f"Current Player: {game_instance.current_player.name}")
        if current_scores.get('ko_point'): # Use ko_point from get_scores
            print(f"Ko Restriction Point: {current_scores['ko_point']}")
        print(f"Captures - BLACK: {current_scores.get('black_captures', 0)}, WHITE: {current_scores.get('white_captures', 0)}")
        print(f"Consecutive Passes: {game_instance.consecutive_passes}") # Direct access is fine
    else:
        print("Final Scores:")
        black_score = current_scores.get('black_score', 'N/A')
        white_score = current_scores.get('white_score', 'N/A')
        komi = current_scores.get('komi', game_instance.komi)
        print(f"  BLACK: {black_score}")
        print(f"  WHITE: {white_score} (Komi: {komi})")
        if isinstance(black_score, (int, float)) and isinstance(white_score, (int, float)):
            if black_score > white_score: print("Winner: BLACK")
            elif white_score > black_score: print("Winner: WHITE")
            else: print("Result: Draw")
        else: print("Result: Scores not available to determine winner.")
    print("="*20 + "\n")

def main():
    print("Welcome to Baduk (Go)!")
    board_size = 19
    try:
        size_input = input(f"Enter board size (e.g., 9, 13, 19, default is 19): ")
        if size_input.strip():
            board_size = int(size_input)
            if not (5 <= board_size <= 25):
                 print("Invalid size (must be 5-25), using default 19.")
                 board_size = 19
    except ValueError:
        print("Invalid input for size, using default 19.")

    player_black_is_ai = False
    player_white_is_ai = False
    ai_difficulty = "easy"

    print("\nChoose game mode:")
    print("1: Human vs. Human")
    print("2: Human (Black) vs. AI (White)")
    print("3: AI (Black) vs. Human (White)")
    print("4: AI (Black) vs. AI (White)")
    mode_choice = input("Enter mode (1, 2, 3, or 4, default 1): ").strip()

    if mode_choice == '2':
        player_white_is_ai = True
    elif mode_choice == '3':
        player_black_is_ai = True
    elif mode_choice == '4':
        player_black_is_ai = True
        player_white_is_ai = True

    if player_black_is_ai or player_white_is_ai:
        difficulty_choice = input(f"Choose AI difficulty (easy, medium, hard, default easy): ").strip().lower()
        if difficulty_choice in ["medium", "hard"]:
            ai_difficulty = difficulty_choice
        else:
            ai_difficulty = "easy" # Default to easy if input is invalid
        print(f"AI difficulty set to: {ai_difficulty}")

    print("") # Newline
    if mode_choice == '2': print("Playing as Black against AI (White).")
    elif mode_choice == '3': print("Playing as White against AI (Black).")
    elif mode_choice == '4': print(f"Watching AI (Black) vs. AI (White) - Difficulty: {ai_difficulty}.")
    else: print("Playing Human vs. Human.")
    print("") # Newline

    game_instance = Game(
        board_size=board_size,
        komi=6.5, # Standard komi, can be made configurable later
        player_black_is_ai=player_black_is_ai,
        player_white_is_ai=player_white_is_ai,
        ai_difficulty=ai_difficulty
    )

    while not game_instance.game_over:
        print_game_state(game_instance)

        is_ai_turn = game_instance.get_current_ai_player() is not None

        if is_ai_turn:
            game_instance.request_ai_move()
            if player_black_is_ai and player_white_is_ai:
                try:
                    time.sleep(0.5) # Reduced delay for AI vs AI
                except ImportError: pass
            continue

        prompt = f"Player {game_instance.current_player.name}, enter move (row,col), or 'pass', or 'quit': "
        action = input(prompt).strip().lower()

        if action == 'quit':
            print("Quitting game. Thanks for playing!")
            return
        elif action == 'pass':
            game_instance.pass_turn()
        else:
            try:
                parts = action.split(',')
                if len(parts) != 2: raise ValueError("Input must be row,col.")
                row = int(parts[0].strip())
                col = int(parts[1].strip())
                if not game_instance.make_move(row, col):
                    # Error message is printed by make_move or place_stone
                    # print("Move attempt failed. See message above. Try again.") # Redundant
                    pass # Allow loop to continue
            except ValueError as e:
                print(f"Invalid input: {e}. Please use 'row,col', 'pass', or 'quit'.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Try again.")

    print("\n--- Game Finished ---")
    print_game_state(game_instance)
    print("Thanks for playing!")

if __name__ == "__main__":
    main()
