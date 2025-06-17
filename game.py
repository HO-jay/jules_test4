
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

    def calculate_territory_scores(self):
        if not self.game_over:
            pass

        territory_points = {Stone.BLACK: 0, Stone.WHITE: 0}
        visited_empty_points = set()

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
                        territory_points[owner] += len(current_empty_region)

        black_total_score = territory_points[Stone.BLACK] + self.captures[Stone.BLACK]
        white_total_score = territory_points[Stone.WHITE] + self.captures[Stone.WHITE] + self.komi

        self.final_scores = {
            Stone.BLACK: {'total': black_total_score, 'territory': territory_points[Stone.BLACK], 'captures': self.captures[Stone.BLACK]},
            Stone.WHITE: {'total': white_total_score, 'territory': territory_points[Stone.WHITE], 'captures': self.captures[Stone.WHITE], 'komi_added': self.komi}
        }

    def pass_turn(self) -> tuple[bool, str]:
        if self.game_over:
            return False, "Game is already over."

        passed_player_name = self.current_player.name
        self.consecutive_passes += 1
        self.ko_restriction_point = None

        message = f"Player {passed_player_name} passed. "
        if self.consecutive_passes >= 2:
            self.game_over = True
            self.calculate_territory_scores()
            message += "Both players passed consecutively. Game over."
        else:
            self.switch_player()
            message += f"{self.current_player.name}'s turn."
        return True, message

    def make_move(self, row: int, col: int) -> tuple[bool, str]:
        if self.game_over:
            return False, "Game is over. No more moves allowed."

        if self.ko_restriction_point is not None and self.ko_restriction_point == (row, col):
            return False, f"Invalid move at ({row},{col}): Illegal due to Ko rule. Point {self.ko_restriction_point} is restricted."

        success, board_message, captured_count, captured_single_stone_coord = self.board.place_stone(row, col, self.current_player)

        if not success:
            return False, board_message

        player_making_move = self.current_player
        print(f"DEBUG_GAME: make_move by {player_making_move} (id: {id(player_making_move)})")
        print(f"DEBUG_GAME: Stone.BLACK id: {id(Stone.BLACK)}, Stone.WHITE id: {id(Stone.WHITE)}")
        print(f"DEBUG_GAME: Before update: self.captures = {self.captures}, captured_count = {captured_count}")

        if player_making_move not in self.captures:
            self.captures[player_making_move] = 0
            print(f"DEBUG_GAME: WARNING - Initialized captures for {player_making_move} in make_move")

        self.captures[player_making_move] += captured_count
        print(f"DEBUG_GAME: After update: self.captures = {self.captures}")

        self.consecutive_passes = 0

        if captured_count == 1 and captured_single_stone_coord is not None:
            self.ko_restriction_point = captured_single_stone_coord
        else:
            self.ko_restriction_point = None

        self.switch_player()

        success_message = f"Move by {player_making_move.name} at ({row},{col}) successful."
        if captured_count > 0:
            success_message += f" Captured {captured_count} stone(s)."
        return True, success_message

    def get_board_display_string(self) -> str:
        display_str = "   " + " ".join([f"{i:2}" for i in range(self.board.size)]) + "\n"
        for r_idx, row_data in enumerate(self.board._grid):
            display_str += f"{r_idx:2} "
            row_str = []
            for stone in row_data:
                if stone == Stone.EMPTY: row_str.append(".")
                elif stone == Stone.BLACK: row_str.append("B")
                elif stone == Stone.WHITE: row_str.append("W")
            display_str += "  ".join(row_str) + "\n"
        if self.ko_restriction_point and not self.game_over:
            display_str += f"Ko restriction at: {self.ko_restriction_point}\n"
        if self.game_over:
            display_str += "\nGAME OVER\n"
        return display_str

    def get_scores(self) -> dict:
        if self.final_scores:
            return {
                'black_score_total': self.final_scores[Stone.BLACK]['total'],
                'black_score_territory': self.final_scores[Stone.BLACK]['territory'],
                'black_score_captures': self.final_scores[Stone.BLACK]['captures'],
                'white_score_total': self.final_scores[Stone.WHITE]['total'],
                'white_score_territory': self.final_scores[Stone.WHITE]['territory'],
                'white_score_captures': self.final_scores[Stone.WHITE]['captures'],
                'komi_applied': self.final_scores[Stone.WHITE]['komi_added'],
                'game_over': self.game_over,
                'scoring_method': 'Territory'
            }
        else:
            return {
                'black_captures_current': self.captures[Stone.BLACK],
                'white_captures_current': self.captures[Stone.WHITE],
                'komi_setting': self.komi,
                'game_over': self.game_over,
                'current_player': self.current_player.name,
                'ko_restriction_point': self.ko_restriction_point,
                'consecutive_passes': self.consecutive_passes,
                'status': 'Game in progress or scores not yet calculated.',
                'scoring_method': 'Territory'
            }

    def get_current_ai_player(self) -> AIOpponent | None:
        if self.current_player == Stone.BLACK and self.player_black_is_ai:
            return self.ai_black
        elif self.current_player == Stone.WHITE and self.player_white_is_ai:
            return self.ai_white
        return None

    def request_ai_move(self) -> tuple[bool, str]:
        ai_player_instance = self.get_current_ai_player()
        if not ai_player_instance or self.game_over:
            return False, "Not AI's turn or game over."

        candidate_coords = []
        for r in range(self.board.size):
            for c in range(self.board.size):
                if self.board.is_empty(r, c) and (r, c) != self.ko_restriction_point:
                    candidate_coords.append((r, c))

        if not candidate_coords:
            return self.pass_turn()

        chosen_move = ai_player_instance.get_move(candidate_coords, self.board)

        if chosen_move is None:
            return self.pass_turn()

        r_move, c_move = chosen_move
        return self.make_move(r_move, c_move)

if __name__ == '__main__':
    print("\n--- Basic Game Run with AI (Territory Scoring Example) ---")
    game = Game(5, player_white_is_ai=True, ai_difficulty="medium")

    human_moves = [(0,0), (1,1), (2,2), (3,0)]
    current_player_is_human = True

    for i in range(10):
        if game.game_over: break
        print(f"Turn {i+1}. Player: {game.current_player.name}")

        success, message = False, ""
        if game.get_current_ai_player():
            print(f"AI ({game.current_player.name}) is thinking...")
            success, message = game.request_ai_move()
            print(f"AI action: {message}")
        else:
            if human_moves:
                r,c = human_moves.pop(0)
                print(f"Human ({game.current_player.name}) plays at ({r},{c})")
                success, message = game.make_move(r,c)
                print(f"Human move result: {message}")
            else:
                print(f"Human ({game.current_player.name}) passes (no more scripted moves).")
                success, message = game.pass_turn()
                print(f"Human pass result: {message}")

        if not success:
            print(f"Move attempt failed. Message: {message}")

    if not game.game_over:
        print("\nGame example finished by turn limit or error.")
        game.game_over = True
        game.calculate_territory_scores()

    print(game.get_board_display_string())
    final_scores = game.get_scores()
    print(f"Final scores: {final_scores}")
