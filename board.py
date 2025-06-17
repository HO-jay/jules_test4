
from stone import Stone

class Board:
    def __init__(self, size: int = 19):
        self.size = size
        self._grid = [[Stone.EMPTY for _ in range(size)] for _ in range(size)]

    def _is_valid_coordinate(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def _remove_stone_group(self, group_stones: set[tuple[int, int]]) -> tuple[int, tuple[int, int] | None]:
        count = len(group_stones)
        single_stone_coord = None
        if count == 1:
            single_stone_coord = list(group_stones)[0]

        for r, c in group_stones:
            self._grid[r][c] = Stone.EMPTY
        return count, single_stone_coord

    def place_stone(self, row: int, col: int, stone_color: Stone) -> tuple[bool, str, int, tuple[int,int] | None]:
        # 1. Validate move (bounds, empty)
        if not self._is_valid_coordinate(row, col):
            return False, "Move out of bounds", 0, None
        if self.get_stone(row,col) != Stone.EMPTY:
            return False, "Intersection is already occupied", 0, None

        # 2. Tentatively place the stone
        self._grid[row][col] = stone_color

        total_opponent_stones_captured = 0
        last_captured_single_coord_for_ko = None

        # 3. Check and remove opponent groups with 0 liberties
        opponent_color = Stone.WHITE if stone_color == Stone.BLACK else Stone.BLACK
        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
            nr, nc = row + dr, col + dc
            if self._is_valid_coordinate(nr, nc) and self.get_stone(nr, nc) == opponent_color:
                group_stones, group_liberties = self.get_group(nr, nc)
                if not group_liberties:
                    count, single_coord = self._remove_stone_group(group_stones)
                    total_opponent_stones_captured += count
                    if count == 1 and single_coord:
                        last_captured_single_coord_for_ko = single_coord

        # 4. Check the placed stone's own group for suicide
        own_group_stones, own_group_liberties = self.get_group(row, col)

        if not own_group_liberties:
            if total_opponent_stones_captured > 0:
                # Valid move because it captured.
                pass
            else:
                # Invalid simple suicide: no opponent stones were captured.
                self._grid[row][col] = Stone.EMPTY # Revert the placement
                return False, "Move is suicidal and captures no stones", 0, None

        return True, "Move successful", total_opponent_stones_captured, last_captured_single_coord_for_ko

    def get_stone(self, row: int, col: int) -> Stone:
        if not self._is_valid_coordinate(row, col):
            raise IndexError("Coordinates out of bounds")
        return self._grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        return self.get_stone(row, col) == Stone.EMPTY

    def get_group(self, row: int, col: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        start_stone_color = self.get_stone(row, col)
        if start_stone_color == Stone.EMPTY:
            return set(), set()
        group_stones = set(); group_liberties = set(); queue = [(row, col)]; visited = set()
        while queue:
            r_curr, c_curr = queue.pop(0) # Renamed to avoid conflict with outer scope if any
            if (r_curr, c_curr) in visited: continue
            visited.add((r_curr,c_curr))
            current_stone_color_at_pos = self.get_stone(r_curr,c_curr)
            if current_stone_color_at_pos != start_stone_color: continue
            group_stones.add((r_curr, c_curr))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r_curr + dr, c_curr + dc
                if self._is_valid_coordinate(nr, nc):
                    neighbor_stone = self.get_stone(nr, nc)
                    if neighbor_stone == start_stone_color:
                        if (nr, nc) not in visited: queue.append((nr, nc))
                    elif neighbor_stone == Stone.EMPTY: group_liberties.add((nr, nc))
        return group_stones, group_liberties

    def get_all_groups_of_color(self, stone_color_param):
        groups = []; visited_stones_for_all_groups = set()
        for r_iter in range(self.size):
            for c_iter in range(self.size):
                if (r_iter, c_iter) in visited_stones_for_all_groups: continue
                current_stone_on_board = self.get_stone(r_iter, c_iter)
                if current_stone_on_board == stone_color_param:
                    group_stones, group_liberties = self.get_group(r_iter, c_iter)
                    if group_stones:
                        groups.append({'stones': group_stones, 'liberties': group_liberties})
                        visited_stones_for_all_groups.update(group_stones)
        return groups
