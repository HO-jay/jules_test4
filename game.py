
from board import Board
from stone import Stone
from ai import AIOpponent
import random

class Game:
    def __init__(self, board_size: int = 19, komi: float = 6.5, player_black_is_ai: bool = False, player_white_is_ai: bool = False, ai_difficulty: str = "easy"):
        self.board = Board(board_size)
        self.current_player = Stone.BLACK
        self.captures = {Stone.BLACK: 0, Stone.WHITE: 0}
        self.komi = komi
        self.ko_restriction_point = None
        self.consecutive_passes = 0
        self.game_over = False
        self.final_scores = None

        self.player_black_is_ai = player_black_is_ai
        self.player_white_is_ai = player_white_is_ai
        self.ai_black = None
        self.ai_white = None

        if self.player_black_is_ai:
            self.ai_black = AIOpponent(Stone.BLACK, ai_difficulty)
        if self.player_white_is_ai:
            self.ai_white = AIOpponent(Stone.WHITE, ai_difficulty)

    def switch_player(self):
        if self.current_player == Stone.BLACK:
            self.current_player = Stone.WHITE
        else:
            self.current_player = Stone.BLACK

    def calculate_area_scores(self) -> dict | None:
        if not self.game_over:
            # print("Game is not over yet. Scores can only be calculated at the end.") # Less verbose
            return None

        scores = {Stone.BLACK: 0, Stone.WHITE: 0}
        visited_empty_points = set()

        for r in range(self.board.size):
            for c in range(self.board.size):
                stone = self.board.get_stone(r, c)
                if stone == Stone.BLACK:
                    scores[Stone.BLACK] += 1
                elif stone == Stone.WHITE:
                    scores[Stone.WHITE] += 1

        for r_start in range(self.board.size):
            for c_start in range(self.board.size):
                if self.board.get_stone(r_start, c_start) == Stone.EMPTY and (r_start, c_start) not in visited_empty_points:
                    current_empty_region = set()
                    border_colors = set()
                    q = [(r_start, c_start)]
                    bfs_visited_this_region = set([(r_start, c_start)])

                    while q:
                        curr_r, curr_c = q.pop(0)
                        current_empty_region.add((curr_r, curr_c))

                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = curr_r + dr, curr_c + dc

                            if self.board._is_valid_coordinate(nr, nc):
                                neighbor_stone = self.board.get_stone(nr, nc)
                                if neighbor_stone == Stone.EMPTY:
                                    if (nr, nc) not in bfs_visited_this_region:
                                        bfs_visited_this_region.add((nr, nc))
                                        q.append((nr, nc))
                                else:
                                    border_colors.add(neighbor_stone)

                    visited_empty_points.update(current_empty_region)

                    if len(border_colors) == 1:
                        owner = list(border_colors)[0]
                        scores[owner] += len(current_empty_region)
        scores[Stone.WHITE] += self.komi
        self.final_scores = scores
        # print(f"Final Scores (Area Scoring, Komi={self.komi}): BLACK: {scores[Stone.BLACK]}, WHITE: {scores[Stone.WHITE]}") # Less verbose for lib
        return scores

    def pass_turn(self) -> bool:
        if self.game_over:
            # print("Game is already over.") # Less verbose for lib
            return False

        self.consecutive_passes += 1
        self.ko_restriction_point = None
        print(f"{self.current_player.name} passed.") # This print is fine for TUI interaction

        if self.consecutive_passes >= 2:
            self.game_over = True
            print("Both players passed consecutively. Game over.")
            self.calculate_area_scores()
        else:
            self.switch_player()
        return True

    def make_move(self, row: int, col: int) -> bool:
        if self.game_over:
            # print("Game is over. No more moves allowed.") # Less verbose for lib
            return False

        if self.ko_restriction_point is not None and self.ko_restriction_point == (row, col):
            # print(f"Invalid move at ({row},{col}): Illegal due to Ko rule. Point {self.ko_restriction_point} is restricted.") # Less verbose
            return False

        try:
            captured_count, captured_single_stone_coord = self.board.place_stone(row, col, self.current_player)
            self.captures[self.current_player] += captured_count

            if captured_count == 1 and captured_single_stone_coord is not None:
                self.ko_restriction_point = captured_single_stone_coord
            else:
                self.ko_restriction_point = None

            self.consecutive_passes = 0
            self.switch_player()
            return True
        except ValueError as e:
            # print(f"Invalid move at ({row},{col}): {e}") # Less verbose for lib
            self.ko_restriction_point = None # Ensure Ko cleared on any invalid move error
            return False
        except IndexError as e:
            # print(f"Error making move at ({row},{col}): {e}") # Less verbose for lib
            self.ko_restriction_point = None
            return False

    def get_board_display_string(self) -> str:
        # ... (content as before, assumed correct) ...
        display_str = "   " + " ".join([f"{i:2}" for i in range(self.board.size)]) + "\n"
        for r_idx, row_data in enumerate(self.board._grid):
            display_str += f"{r_idx:2} "
            row_str = []
            for stone in row_data:
                if stone == Stone.EMPTY: row_str.append(".")
                elif stone == Stone.BLACK: row_str.append("B")
                elif stone == Stone.WHITE: row_str.append("W")
            display_str += "  ".join(row_str) + "\n"
        if self.ko_restriction_point:
            display_str += f"Ko restriction at: {self.ko_restriction_point}\n"
        if self.game_over:
            display_str += "\nGAME OVER\n"
        return display_str


    def get_scores(self) -> dict:
        if self.final_scores:
            return {
                "black_score": self.final_scores.get(Stone.BLACK, 0),
                "white_score": self.final_scores.get(Stone.WHITE, 0),
                "komi": self.komi,
                "game_over": self.game_over
            }
        else:
            return {
                "black_captures": self.captures[Stone.BLACK],
                "white_captures": self.captures[Stone.WHITE],
                "komi": self.komi,
                "game_over": self.game_over,
                "current_player": self.current_player.name, # Keep for TUI
                "status": "Scores not yet calculated (game may not be over)"
            }

    def get_current_ai_player(self) -> AIOpponent | None:
        if self.current_player == Stone.BLACK and self.player_black_is_ai:
            return self.ai_black
        elif self.current_player == Stone.WHITE and self.player_white_is_ai:
            return self.ai_white
        return None

    def request_ai_move(self):
        """
        If the current player is an AI, this method gets a move from the AI,
        validates it by trying to play it. If AI's choice is invalid (e.g., suicidal),
        this version relies on AI to pick a non-suicidal one from candidates or pass.
        If AI passes or has no valid moves, game.pass_turn() is called.
        """
        ai_player_instance = self.get_current_ai_player()
        if not ai_player_instance or self.game_over:
            return False

        print(f"AI ({self.current_player.name}) is thinking (Difficulty: {ai_player_instance.difficulty})...")

        candidate_coords = []
        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.board.is_empty(r, c) and (r, c) != self.ko_restriction_point:
                    candidate_coords.append((r, c))

        if not candidate_coords:
            print(f"AI ({ai_player_instance.ai_stone_color.name}) found no candidate spots and passes.")
            self.pass_turn()
            return True

        chosen_move = ai_player_instance.get_move(candidate_coords, self.board)

        if chosen_move is None:
            print(f"AI ({ai_player_instance.ai_stone_color.name}) chooses to pass.")
            self.pass_turn()
            return True

        r_move, c_move = chosen_move
        # The AI's get_move should ideally return a move that it knows is not suicidal.
        # The make_move method will raise ValueError for suicidal moves, which should be handled by TUI or calling logic.
        # For AI, if it picks a suicidal move (despite its internal check), it's an AI flaw.
        # The Game's make_move will prevent it.
        if self.make_move(r_move, c_move):
            # Successful move by AI. TUI will print board. Game class should not print AI's move directly.
            # print(f"AI ({ai_player_instance.ai_stone_color.name}) played at {chosen_move}") # This is TUI's job
            return True
        else:
            # This implies the AI's chosen move was invalid (e.g. suicidal, or Ko if AI didn't check Ko, but Game does)
            # make_move would have printed the error.
            print(f"AI ({ai_player_instance.ai_stone_color.name}) selected move {chosen_move} which was ultimately invalid. AI passes.")
            self.pass_turn()
            return True

if __name__ == '__main__':
    # ... (main block as it was after previous AI integration, or a simplified one for brevity) ...
    print("\n--- Basic Game Run with AI (Example) ---")
    game = Game(5, player_white_is_ai=True, ai_difficulty="medium")

    # Example game play
    human_moves = [(0,0), (1,1), (2,2), (3,3), (4,4)] # Example moves for Black (Human)
    for i in range(5): # Limit turns for this example
        if game.game_over: break

        # Human (Black) turn
        if game.current_player == Stone.BLACK and not game.player_black_is_ai:
            if i < len(human_moves):
                r,c = human_moves[i]
                print(f"Player BLACK (Human) plays at ({r},{c})")
                game.make_move(r,c)
                print(game.get_board_display_string())
            else: # Human ran out of scripted moves, pass
                print("Player BLACK (Human) passes.")
                game.pass_turn()

        if game.game_over: break

        # AI (White) turn
        if game.current_player == Stone.WHITE and game.player_white_is_ai:
            print("Requesting AI White's move...")
            game.request_ai_move()
            print(game.get_board_display_string())

    if not game.game_over:
        print("\nGame example finished by turn limit.")
        game.game_over = True # Force game over to see scores
        game.calculate_area_scores()

    final_scores = game.get_scores()
    print(f"Final scores: {final_scores}")
