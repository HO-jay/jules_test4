
import unittest
import sys
import os

# Adjust path to import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from board import Board
from stone import Stone

class TestBoard(unittest.TestCase):
    def test_board_initialization(self):
        board = Board(size=9)
        self.assertEqual(board.size, 9)
        self.assertEqual(len(board._grid), 9)
        self.assertTrue(all(all(cell == Stone.EMPTY for cell in row) for row in board._grid))

        board_default = Board()
        self.assertEqual(board_default.size, 19)

    def test_place_stone_valid(self):
        board = Board(size=5)
        board.place_stone(2, 2, Stone.BLACK)
        self.assertEqual(board.get_stone(2, 2), Stone.BLACK)

    def test_place_stone_out_of_bounds(self):
        board = Board(size=5)
        with self.assertRaisesRegex(ValueError, "Move out of bounds"):
            board.place_stone(5, 2, Stone.BLACK)
        with self.assertRaisesRegex(ValueError, "Move out of bounds"):
            board.place_stone(-1, 2, Stone.BLACK)

    def test_place_stone_occupied(self):
        board = Board(size=5)
        board.place_stone(2, 2, Stone.BLACK)
        with self.assertRaisesRegex(ValueError, "Intersection is already occupied"):
            board.place_stone(2, 2, Stone.WHITE)

    def test_get_stone_out_of_bounds(self):
        board = Board(size=5)
        with self.assertRaises(IndexError): # Current get_stone raises IndexError
            board.get_stone(5,2)

    def test_is_empty(self):
        board = Board(size=5)
        self.assertTrue(board.is_empty(0,0))
        board.place_stone(0,0,Stone.BLACK)
        self.assertFalse(board.is_empty(0,0))

    def test_get_group_single_stone(self):
        board = Board(size=5)
        board.place_stone(2, 2, Stone.BLACK)
        group_stones, group_liberties = board.get_group(2, 2)
        self.assertEqual(group_stones, {(2, 2)})
        self.assertEqual(len(group_liberties), 4) # (1,2), (3,2), (2,1), (2,3)
        self.assertIn((1,2), group_liberties)

    def test_get_group_multiple_stones(self):
        board = Board(size=5)
        board.place_stone(0, 0, Stone.BLACK)
        board.place_stone(0, 1, Stone.BLACK)
        board.place_stone(1, 0, Stone.BLACK)
        # B B .
        # B . .
        # . . .
        group_stones, group_liberties = board.get_group(0, 0)
        expected_stones = {(0,0), (0,1), (1,0)}
        # After placing (0,0)B, (0,1)B, (1,0)B on 5x5:
        # Liberties: (0,2), (1,1), (2,0)
        self.assertEqual(group_stones, expected_stones)
        self.assertEqual(group_liberties, {(1,1), (0,2), (2,0)})


    def test_get_group_empty_point(self):
        board = Board(size=5)
        group_stones, group_liberties = board.get_group(2, 2)
        self.assertEqual(group_stones, set())
        self.assertEqual(group_liberties, set())

    def test_simple_capture(self):
        # . B .
        # B W B
        # . B .
        board = Board(size=5) # Reset board for clarity
        board.place_stone(1,1, Stone.WHITE) # W at center
        board.place_stone(0,1, Stone.BLACK) # B above
        board.place_stone(1,0, Stone.BLACK) # B left
        board.place_stone(1,2, Stone.BLACK) # B right

        # Last black stone to capture white stone at (1,1)
        captured_count, _ = board.place_stone(2,1, Stone.BLACK) # B below

        self.assertEqual(captured_count, 1)
        self.assertTrue(board.is_empty(1,1))
        self.assertEqual(board.get_stone(2,1), Stone.BLACK) # Ensure capturing stone is there

    def test_no_capture_if_liberties(self):
        board = Board(size=5)
        board.place_stone(1,1, Stone.WHITE)
        board.place_stone(0,1, Stone.BLACK)
        board.place_stone(1,0, Stone.BLACK)
        # White stone at (1,1) still has 2 liberties: (1,2) and (2,1)
        captured_count, _ = board.place_stone(2,2, Stone.BLACK) # A non-adjacent black stone
        self.assertEqual(captured_count, 0)
        self.assertEqual(board.get_stone(1,1), Stone.WHITE)

    def test_suicide_illegal_simple(self):
        # Setup:
        # B B B
        # B . B  (Target for W is (1,1))
        # B B E  (E at (2,2) is a liberty for the Black group)
        board_suicide = Board(size=3)
        board_suicide.place_stone(0,0, Stone.BLACK)
        board_suicide.place_stone(0,1, Stone.BLACK)
        board_suicide.place_stone(0,2, Stone.BLACK)
        board_suicide.place_stone(1,0, Stone.BLACK)
        # (1,1) is EMPTY
        board_suicide.place_stone(1,2, Stone.BLACK)
        board_suicide.place_stone(2,0, Stone.BLACK)
        board_suicide.place_stone(2,1, Stone.BLACK)
        # (2,2) is left EMPTY as a liberty for the black group

        with self.assertRaisesRegex(ValueError, "Move is suicidal and not allowed"):
            board_suicide.place_stone(1,1,Stone.WHITE) # W plays into the surrounded spot
        self.assertTrue(board_suicide.is_empty(1,1)) # Ensure stone was not placed or was removed by suicide handling


if __name__ == '__main__':
    unittest.main()
