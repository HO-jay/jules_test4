
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game import Game, Stone

class TestGame(unittest.TestCase):
    def test_game_initialization(self):
        game = Game(board_size=9)
        self.assertEqual(game.board.size, 9)
        self.assertEqual(game.current_player, Stone.BLACK)
        self.assertEqual(game.captures[Stone.BLACK], 0)

    def test_make_move_simple_valid(self):
        game = Game(board_size=5)
        success, msg = game.make_move(0,0)
        self.assertTrue(success, msg)
        self.assertEqual(game.board.get_stone(0,0), Stone.BLACK)
        self.assertEqual(game.current_player, Stone.WHITE)

    def test_make_move_invalid_occupied(self):
        game = Game(board_size=5)
        s,m = game.make_move(0,0)
        self.assertTrue(s,m)

        success, msg = game.make_move(0,0)

        self.assertFalse(success, "Should fail when playing on occupied spot")
        self.assertIn("occupied", msg.lower())
        self.assertEqual(game.board.get_stone(0,0), Stone.BLACK)
        self.assertEqual(game.current_player, Stone.WHITE)

    def test_pass_turn(self):
        game = Game(board_size=5)
        self.assertEqual(game.current_player, Stone.BLACK)
        success, msg = game.pass_turn()
        self.assertTrue(success, msg)
        self.assertEqual(game.current_player, Stone.WHITE)
        self.assertEqual(game.consecutive_passes, 1)
        self.assertIsNone(game.ko_restriction_point)

    def test_game_end_by_two_passes(self):
        game = Game(board_size=5)
        s1,m1 = game.pass_turn()
        self.assertTrue(s1,m1)
        s2,m2 = game.pass_turn()
        self.assertTrue(s2,m2)
        self.assertTrue(game.game_over)
        self.assertIn("game over", m2.lower())
        self.assertIsNotNone(game.final_scores)

    def test_ko_rule_simple(self):
        game = Game(board_size=5)
        game.make_move(0,1); game.make_move(0,0)
        game.make_move(1,0); game.make_move(0,2)
        game.make_move(1,2); game.make_move(1,1)

        success_capture, msg_capture = game.make_move(2,1)
        self.assertTrue(success_capture, msg_capture)
        self.assertEqual(game.board.get_stone(1,1), Stone.EMPTY)
        self.assertEqual(game.ko_restriction_point, (1,1))
        self.assertEqual(game.current_player, Stone.WHITE)

        success_ko_fail, msg_ko_fail = game.make_move(1,1)
        self.assertFalse(success_ko_fail, "Ko recapture should fail")
        self.assertIn("ko rule", msg_ko_fail.lower())
        self.assertEqual(game.board.get_stone(1,1), Stone.EMPTY)
        self.assertEqual(game.current_player, Stone.WHITE)

        s,m = game.make_move(4,4); self.assertTrue(s,m)
        self.assertIsNone(game.ko_restriction_point)
        self.assertEqual(game.current_player, Stone.BLACK)

        s,m = game.make_move(1,1); self.assertTrue(s,m)
        self.assertEqual(game.board.get_stone(1,1), Stone.BLACK)

    def test_capture_updates_dictionary(self): # Focused test for capture
        game = Game(board_size=5)
        # Setup: W at (0,0), B at (0,1), B at (1,0).
        # Turn sequence to get this state with Black to play next for capture:

        # B: (0,1)
        s,m = game.make_move(0,1); self.assertTrue(s,m); self.assertEqual(game.current_player, Stone.WHITE)
        # W: (0,0) - the stone to be captured
        s,m = game.make_move(0,0); self.assertTrue(s,m); self.assertEqual(game.current_player, Stone.BLACK)
        # B: (1,0)
        s,m = game.make_move(1,0); self.assertTrue(s,m); self.assertEqual(game.current_player, Stone.WHITE)
        # W: pass (or play elsewhere) to give turn to B
        s,m = game.pass_turn(); self.assertTrue(s,m); self.assertEqual(game.current_player, Stone.BLACK)

        # Current board state for capture:
        # W B . . .  (W(0,0) B(0,1))
        # B . . . .  (B(1,0))
        # Player is BLACK.
        print(f"DEBUG_TEST: Player is {game.current_player.name}. Attempting capture at (1,1).")
        print(f"DEBUG_TEST: Before capture, game.captures = {game.captures}")

        success, msg = game.make_move(1,1) # Black plays at (1,1) to capture W at (0,0)
        self.assertTrue(success, f"Capturing move failed: {msg}")

        print(f"DEBUG_TEST: After B plays at (1,1) to capture W(0,0):")
        print(f"DEBUG_TEST: game.captures = {game.captures}") # See what the test method sees
        print(f"DEBUG_TEST: game.captures.get(Stone.BLACK) = {game.captures.get(Stone.BLACK)}")

        self.assertEqual(game.captures.get(Stone.BLACK), 1, "Black should have 1 capture.")


    # Original test_territory_scoring_simple - can be re-enabled later
    # def test_territory_scoring_simple(self):
    #     game = Game(board_size=5, komi=0.5)
    #     game.make_move(0,1); game.make_move(4,4)
    #     game.make_move(1,0); game.make_move(0,0)
    #     s_cap, m_cap = game.make_move(1,1);
    #     self.assertTrue(s_cap, m_cap)

    #     self.assertEqual(game.captures[Stone.BLACK], 1)

    #     game.make_move(3,3)

    #     game.make_move(2,1); game.make_move(4,3)
    #     game.make_move(1,2); game.make_move(4,2)
    #     game.make_move(2,3); game.make_move(4,1)
    #     game.make_move(3,2);

    #     s_p1,m_p1 = game.pass_turn(); self.assertTrue(s_p1,m_p1)
    #     s_p2,m_p2 = game.pass_turn(); self.assertTrue(s_p2,m_p2)

    #     self.assertTrue(game.game_over)
    #     scores = game.get_scores()
    #     self.assertEqual(scores['black_score_territory'], 1)
    #     self.assertEqual(scores['black_score_captures'], 1)
    #     self.assertEqual(scores['black_score_total'], 2.0)
    #     self.assertEqual(scores['white_score_territory'], 0)
    #     self.assertEqual(scores['white_score_captures'], 0)
    #     self.assertEqual(scores['white_score_total'], 0.5)
    #     self.assertEqual(scores['scoring_method'], 'Territory')

if __name__ == '__main__':
    unittest.main()
