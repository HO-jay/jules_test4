
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from board import Board
from stone import Stone

class TestBoard(unittest.TestCase):
    def test_board_initialization(self):
        board = Board(size=9)
        self.assertEqual(board.size, 9)
        success, _, _, _ = board.place_stone(0,0,Stone.BLACK)
        self.assertTrue(success)

    def test_place_stone_valid(self):
        board = Board(size=5)
        success, msg, captured_count, ko_coord = board.place_stone(2, 2, Stone.BLACK)
        self.assertTrue(success, f"Placement should be valid. Msg: {msg}")
        self.assertEqual(board.get_stone(2, 2), Stone.BLACK)
        self.assertEqual(captured_count, 0)
        self.assertIsNone(ko_coord)

    def test_place_stone_out_of_bounds(self):
        board = Board(size=5)
        success, msg, _, _ = board.place_stone(5, 2, Stone.BLACK)
        self.assertFalse(success)
        self.assertIn("Move out of bounds", msg)
        success, msg, _, _ = board.place_stone(-1, 2, Stone.BLACK)
        self.assertFalse(success)
        self.assertIn("Move out of bounds", msg)

    def test_place_stone_occupied(self):
        board = Board(size=5)
        s1,_,_,_ = board.place_stone(2, 2, Stone.BLACK)
        self.assertTrue(s1)
        success, msg, _, _ = board.place_stone(2, 2, Stone.WHITE)
        self.assertFalse(success)
        self.assertIn("Intersection is already occupied", msg)

    def test_get_stone_out_of_bounds(self):
        board = Board(size=5)
        with self.assertRaises(IndexError):
            board.get_stone(5,2)

    def test_is_empty(self):
        board = Board(size=5)
        self.assertTrue(board.is_empty(0,0))
        s,_,_,_ = board.place_stone(0,0,Stone.BLACK)
        self.assertTrue(s)
        self.assertFalse(board.is_empty(0,0))

    def test_get_group_single_stone(self):
        board = Board(size=5)
        s,_,_,_ = board.place_stone(2,2,Stone.BLACK)
        self.assertTrue(s)
        group_stones, group_liberties = board.get_group(2, 2)
        self.assertEqual(group_stones, {(2,2)})
        self.assertEqual(len(group_liberties), 4)

    def test_get_group_multiple_stones(self):
        board = Board(size=5)
        s1,_,_,_ = board.place_stone(0,0,Stone.BLACK)
        s2,_,_,_ = board.place_stone(0,1,Stone.BLACK)
        s3,_,_,_ = board.place_stone(1,0,Stone.BLACK)
        self.assertTrue(s1 and s2 and s3)
        group_stones, group_liberties = board.get_group(0,0)
        self.assertEqual(group_stones, {(0,0),(0,1),(1,0)})
        self.assertEqual(group_liberties, {(0,2),(1,1),(2,0)})

    def test_get_group_empty_point(self):
        board = Board(size=5)
        group_stones, group_liberties = board.get_group(2,2)
        self.assertEqual(group_stones, set())
        self.assertEqual(group_liberties, set())

    def test_simple_capture(self):
        board = Board(size=5)
        s1,_,_,_ = board.place_stone(1,1, Stone.WHITE)
        s2,_,_,_ = board.place_stone(0,1, Stone.BLACK)
        s3,_,_,_ = board.place_stone(1,0, Stone.BLACK)
        s4,_,_,_ = board.place_stone(1,2, Stone.BLACK)
        self.assertTrue(s1 and s2 and s3 and s4)

        success, msg, captured_count, ko_coord = board.place_stone(2,1, Stone.BLACK)
        self.assertTrue(success, f"Capture move should be valid. Msg: {msg}")
        self.assertEqual(captured_count, 1)
        self.assertTrue(board.is_empty(1,1))
        self.assertEqual(ko_coord, (1,1))

    def test_no_capture_if_liberties(self):
        board = Board(size=5)
        s1,_,_,_ = board.place_stone(1,1, Stone.WHITE)
        s2,_,_,_ = board.place_stone(0,1, Stone.BLACK)
        s3,_,_,_ = board.place_stone(1,0, Stone.BLACK)
        self.assertTrue(s1 and s2 and s3)

        success, msg, captured_count, _ = board.place_stone(2,2, Stone.BLACK)
        self.assertTrue(success)
        self.assertEqual(captured_count, 0)
        self.assertEqual(board.get_stone(1,1), Stone.WHITE)

    def test_suicide_rules(self):
        # Test 1: Invalid simple suicide (no captures)
        board = Board(size=3)
        # B B B
        # B . B  (Target for W is (1,1))
        # B B E  (E at (2,2) is a liberty for the Black group)
        s,_,_,_ = board.place_stone(0,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(0,1, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(0,2, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(1,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(1,2, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(2,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(2,1, Stone.BLACK); self.assertTrue(s)
        # (2,2) is left EMPTY as a liberty for the black group

        success, msg, captured_count, ko_coord = board.place_stone(1,1, Stone.WHITE)
        self.assertFalse(success, "Simple suicide should fail")
        self.assertIn("suicidal and captures no stones", msg)
        self.assertEqual(board.get_stone(1,1), Stone.EMPTY, "Board should be reverted on simple suicide")
        self.assertEqual(captured_count, 0)
        self.assertIsNone(ko_coord)

        # Test 2: Valid move because it captures opponent stones (Snapback-like scenario)
        # B W .
        # B X W  X is (1,1) - White to play, captures B stones at (0,1) (no, (1,0) )
        # B W .
        board = Board(size=3)
        # Black stones that form a group to be captured
        s,_,_,_ = board.place_stone(0,0, Stone.BLACK); self.assertTrue(s) # B at (0,0)
        s,_,_,_ = board.place_stone(1,0, Stone.BLACK); self.assertTrue(s) # B at (1,0)
        s,_,_,_ = board.place_stone(2,0, Stone.BLACK); self.assertTrue(s) # B at (2,0)
        # White stones to create the capture point for B group
        s,_,_,_ = board.place_stone(0,1, Stone.WHITE); self.assertTrue(s) # W at (0,1)
        # s,_,_,_ = board.place_stone(1,1, Stone.WHITE); # This is where W will play
        s,_,_,_ = board.place_stone(1,2, Stone.WHITE); self.assertTrue(s) # W at (1,2) # Mistake in prev trace, this W is not needed for this specific capture
        s,_,_,_ = board.place_stone(2,1, Stone.WHITE); self.assertTrue(s) # W at (2,1)
        # Board state before W plays at (1,1):
        # B W .
        # B . .   <-- Mistake in manual board drawing, W at (1,2) is not relevant for this simple column capture.
        # B W .
        # Corrected setup for capturing B column:
        # B W .
        # B _ W  <-- White plays at (1,1)
        # B W .
        # Remove W at (1,2) for this test case to be simpler.
        board = Board(size=3) # Reset for clarity
        s,_,_,_ = board.place_stone(0,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(1,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(2,0, Stone.BLACK); self.assertTrue(s)
        s,_,_,_ = board.place_stone(0,1, Stone.WHITE); self.assertTrue(s)
        s,_,_,_ = board.place_stone(2,1, Stone.WHITE); self.assertTrue(s)
        # Board:
        # B W .
        # B . .
        # B W .
        # White plays at (1,1). This puts B group {(0,0),(1,0),(2,0)} in atari, then captures.

        success, msg, captured_count, ko_coord = board.place_stone(1,1, Stone.WHITE)
        self.assertTrue(success, f"Snapback-like capture should be valid. Msg: {msg}")
        self.assertEqual(board.get_stone(1,1), Stone.WHITE, "Capturing stone should remain")
        self.assertEqual(captured_count, 3, "Should capture 3 black stones")
        self.assertTrue(board.is_empty(1,0)) # Check one of the captured stones

if __name__ == '__main__':
    unittest.main()
