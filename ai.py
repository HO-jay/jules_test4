
import random
import copy
from stone import Stone
from typing import TYPE_CHECKING, List, Tuple, Optional, Set, Dict # Added for type hints
if TYPE_CHECKING:
    from board import Board # For type hinting only

class AIOpponent:
    def __init__(self, ai_stone_color: Stone, difficulty: str ="easy"):
        self.ai_stone_color: Stone = ai_stone_color
        self.difficulty: str = difficulty
        self.opponent_stone_color: Stone = Stone.WHITE if self.ai_stone_color == Stone.BLACK else Stone.BLACK

    def _is_move_suicidal(self, board_instance: 'Board', r: int, c: int, stone_color: Stone) -> bool:
        temp_board = copy.deepcopy(board_instance)
        try:
            temp_board.place_stone(r, c, stone_color)
            return False
        except ValueError as e:
            return "suicidal" in str(e).lower()
        except IndexError:
            return True # Treat out of bounds as invalid/suicidal for safety here

    def get_move(self, candidate_moves: List[Tuple[int,int]], board_instance: 'Board') -> Optional[Tuple[int,int]]:
        """
        Selects a move based on difficulty level.
        Args:
            candidate_moves (list): List of (r,c) tuples pre-filtered (empty, not Ko).
            board_instance (Board): The current game board instance.
        Returns:
            tuple: (r,c) for a chosen move, or None to pass.
        """
        if not candidate_moves:
            return None

        if self.difficulty == "easy":
            non_suicidal_candidates = [
                (r_cand, c_cand) for r_cand, c_cand in candidate_moves
                if not self._is_move_suicidal(board_instance, r_cand, c_cand, self.ai_stone_color)
            ]
            if not non_suicidal_candidates: return None
            return random.choice(non_suicidal_candidates)

        elif self.difficulty == "medium" or self.difficulty == "hard": # Hard is same as medium for now
            capture_moves_found: List[Dict] = []
            for r_cap, c_cap in candidate_moves:
                if self._is_move_suicidal(board_instance, r_cap, c_cap, self.ai_stone_color):
                    continue
                temp_board_for_capture = copy.deepcopy(board_instance)
                try:
                    original_opponent_stones_count = sum(row.count(self.opponent_stone_color) for row in temp_board_for_capture._grid)
                    temp_board_for_capture.place_stone(r_cap, c_cap, self.ai_stone_color)
                    current_opponent_stones_count = sum(row.count(self.opponent_stone_color) for row in temp_board_for_capture._grid)
                    if current_opponent_stones_count < original_opponent_stones_count:
                        capture_moves_found.append({
                            'move': (r_cap, c_cap),
                            'captures': original_opponent_stones_count - current_opponent_stones_count
                        })
                except (ValueError, IndexError): continue

            if capture_moves_found:
                capture_moves_found.sort(key=lambda x: x['captures'], reverse=True)
                return capture_moves_found[0]['move']

            if hasattr(board_instance, 'get_all_groups_of_color'):
                own_groups: List[Dict[str, Set[Tuple[int,int]]]] = board_instance.get_all_groups_of_color(self.ai_stone_color)
                potential_saving_moves: List[Tuple[int,int]] = []
                for group_info in own_groups:
                    if len(group_info['liberties']) == 1:
                        single_liberty_coord = list(group_info['liberties'])[0]
                        if single_liberty_coord in candidate_moves: # Check if filling the liberty is a candidate
                            if not self._is_move_suicidal(board_instance, single_liberty_coord[0], single_liberty_coord[1], self.ai_stone_color):
                                temp_board_for_saving = copy.deepcopy(board_instance)
                                try:
                                    temp_board_for_saving.place_stone(single_liberty_coord[0], single_liberty_coord[1], self.ai_stone_color)
                                    # Check if the original group stones are now part of a group with more liberties
                                    # This needs to check the specific group that was in danger.
                                    # A simple check: if the new stone's group (which includes the saved stone) has > 1 liberty.
                                    # This assumes the liberty point correctly connects to the endangered group.
                                    _ , new_liberties = temp_board_for_saving.get_group(single_liberty_coord[0], single_liberty_coord[1])
                                    if len(new_liberties) > 1:
                                        potential_saving_moves.append(single_liberty_coord)
                                except (ValueError, IndexError): continue
                if potential_saving_moves:
                    return random.choice(potential_saving_moves)

            non_suicidal_candidates_fallback = [
                (r_fall, c_fall) for r_fall, c_fall in candidate_moves
                if not self._is_move_suicidal(board_instance, r_fall, c_fall, self.ai_stone_color)
            ]
            if non_suicidal_candidates_fallback:
                return random.choice(non_suicidal_candidates_fallback)
            return None

        safe_default_candidates = [m for m in candidate_moves if not self._is_move_suicidal(board_instance, m[0], m[1], self.ai_stone_color)]
        return random.choice(safe_default_candidates) if safe_default_candidates else None
