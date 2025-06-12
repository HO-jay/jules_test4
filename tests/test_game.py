
import unittest
import sys
import os

# Adjust path to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game import Game
from board import Board # For direct board manipulation in tests if needed
from stone import Stone

class TestGame(unittest.TestCase):
    def test_game_initialization(self):
        game = Game(board_size=9)
        self.assertEqual(game.board.size, 9)
        self.assertEqual(game.current_player, Stone.BLACK)
        self.assertEqual(game.captures[Stone.BLACK], 0)
        self.assertEqual(game.captures[Stone.WHITE], 0)
        self.assertEqual(game.komi, 6.5) # Default Komi
        self.assertFalse(game.game_over)

    def test_make_move_simple_valid(self):
        game = Game(board_size=5)
        self.assertTrue(game.make_move(0,0))
        self.assertEqual(game.board.get_stone(0,0), Stone.BLACK)
        self.assertEqual(game.current_player, Stone.WHITE)
        self.assertEqual(game.consecutive_passes, 0)

    def test_make_move_invalid_occupied(self):
        game = Game(board_size=5)
        game.make_move(0,0) # Black plays at 0,0
        # Suppress print statements from game.make_move for this test
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            self.assertFalse(game.make_move(0,0)) # White tries to play at 0,0
        finally:
            sys.stdout.close()
            sys.stdout = old_stdout

        self.assertEqual(game.board.get_stone(0,0), Stone.BLACK)
        self.assertEqual(game.current_player, Stone.WHITE)

    def test_pass_turn(self):
        game = Game(board_size=5)
        self.assertEqual(game.current_player, Stone.BLACK)
        game.pass_turn()
        self.assertEqual(game.current_player, Stone.WHITE)
        self.assertEqual(game.consecutive_passes, 1)
        self.assertIsNone(game.ko_restriction_point)

    def test_game_end_by_two_passes(self):
        game = Game(board_size=5)
        game.pass_turn()
        game.pass_turn()
        self.assertTrue(game.game_over)
        self.assertIsNotNone(game.final_scores)

    def test_no_moves_or_pass_after_game_over(self):
        game = Game(board_size=5)
        game.pass_turn()
        game.pass_turn()
        self.assertTrue(game.game_over)

        self.assertFalse(game.make_move(0,0))

        initial_passes = game.consecutive_passes
        self.assertFalse(game.pass_turn())
        self.assertEqual(game.consecutive_passes, initial_passes)

    def test_ko_rule_simple(self):
        game = Game(board_size=5)
        game.make_move(0,1) # B
        game.make_move(0,0) # W
        game.make_move(1,0) # B
        game.make_move(0,2) # W
        game.make_move(1,2) # B
        game.make_move(1,1) # W
        self.assertTrue(game.make_move(2,1)) # B captures W at (1,1)

        self.assertEqual(game.board.get_stone(1,1), Stone.EMPTY)
        self.assertIsNotNone(game.ko_restriction_point)
        self.assertEqual(game.ko_restriction_point, (1,1))
        self.assertEqual(game.current_player, Stone.WHITE)

        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            self.assertFalse(game.make_move(1,1)) # Ko violation
        finally:
            sys.stdout.close()
            sys.stdout = old_stdout

        self.assertEqual(game.board.get_stone(1,1), Stone.EMPTY)
        self.assertEqual(game.current_player, Stone.WHITE)

        self.assertTrue(game.make_move(4,4))
        self.assertIsNone(game.ko_restriction_point)
        self.assertEqual(game.current_player, Stone.BLACK)

        self.assertTrue(game.make_move(1,1))
        self.assertEqual(game.board.get_stone(1,1), Stone.BLACK)

    def test_area_scoring_simple(self):
        game = Game(board_size=5, komi=0.5)

        game.board.place_stone(0,0, Stone.BLACK)
        game.board.place_stone(0,1, Stone.BLACK)
        game.board.place_stone(0,2, Stone.BLACK)
        game.board.place_stone(1,0, Stone.BLACK)
        game.board.place_stone(1,2, Stone.BLACK)
        game.board.place_stone(2,0, Stone.BLACK)
        game.board.place_stone(2,1, Stone.BLACK)
        game.board.place_stone(2,2, Stone.BLACK)

        game.board.place_stone(3,3, Stone.WHITE)
        game.board.place_stone(3,4, Stone.WHITE)
        game.board.place_stone(4,3, Stone.WHITE)
        game.board.place_stone(4,4, Stone.WHITE)

        game.game_over = True
        scores = game.calculate_area_scores()

        self.assertIsNotNone(scores)
        if scores:
            self.assertEqual(scores[Stone.BLACK], 9)
            self.assertEqual(scores[Stone.WHITE], 4.5)

if __name__ == '__main__':
    unittest.main()
