import string
from collections import defaultdict
from itertools import combinations

# Colors & Symbols for grid
SECTION_BGS = [
    40, 191, 218, 172, 63, 226, 45, 105, 249, 188
]
BLACK = 232
WHITE = 196
UNICODE_STAR = "★"
UNICODE_DOT = "·"
UNICODE_SQUARE = '■'


class Tile:
    #
    def __init__(self, pos, section, value):
        if isinstance(pos, tuple):
            self.row, self.col = pos
        else:
            raise ValueError('pos is not a tuple')

        self.section = section
        self.value = value

    def __str__(self):
        return str(self.row + 1) + string.ascii_uppercase[self.col]

    def __eq__(self, other):
        return (
            self.row == other.row and
            self.col == other.col and
            self.value == other.value and
            self.section == other.section
        )

    def __hash__(self):
        return hash((self.row, self.col, self.value, self.section))
    
    __repr__ = __str__

    def copy(self):
        return Tile((self.row, self.col), self.section, self.value)
    
    def empty(self):
        return self.value == '.'


class Group:
    def __init__(self, tiles, stars):
        self.tiles = set(tiles)
        self.stars = stars
    
    # true if this group is a subset of the given list of tiles
    def is_subset(self, tiles):
        for my_tile in self.tiles:
            if my_tile not in tiles:
                return False
        return True

    # return number of tiles in this group contained in the given collection of tiles
    def get_overlap(self, tiles):
        ans = 0
        for my_tile in self.tiles:
            if my_tile in tiles:
                ans += 1
        return ans
    
    def copy(self):
        return Group({tile.copy() for tile in self.tiles}, self.stars)
    
    def __eq__(self, other):
        return self.tiles == other.tiles and self.stars == other.stars
    
    def remove_tile(self, tile):
        try:
            self.tiles.remove(tile)
        except KeyError:
            pass

    def __hash__(self):
        return hash(tuple(self.tiles))

    def __repr__(self):
        return f'Group({self.tiles}, {self.stars})'

    def empty(self):
        return len(self.tiles) == 0

    def contains(self, tile):
        return tile in self.tiles

# return a set of all tiles in any of the groups passed
def group_union(groups):
    tile_set = set()
    for group in groups:
        tile_set |= group.tiles
    return tile_set

# return a set of all tiles in all the groups passed
def group_conjunction(groups):
    tile_set = set()
    first = True
    if len(groups) == 1:
        return set()
    for group in groups:
        if first:
            tile_set = group.tiles.copy()
            first = False
        else:
            tile_set &= group.tiles
    return tile_set

class Square:
    def __init__(self, size, start_tile):
        self.tiles = {start_tile}
        self.max = (start_tile.row, start_tile.col)
        self.min = self.max
        self.size = size

    def offer(self, tile):
        new_max = (max(self.max[0], tile.row), max(self.max[1], tile.col))
        new_min = (min(self.min[0], tile.row), min(self.min[1], tile.col))
        x_diff = new_max[0] - new_min[0]
        y_diff = new_max[1] - new_min[1]
        if x_diff >= self.size or y_diff >= self.size:
            return False
        else:
            self.tiles.add(tile)
            self.min = new_min
            self.max = new_max
            return True

def get_2x2_groups(tiles):
    tiles = sorted(tiles, key=lambda tile: tile.row + tile.col)
    squares = []
    for tile in tiles:
        for square in squares:
            if square.offer(tile):
                break
        else:
            squares.append(Square(2, tile))
    ans = [s.tiles for s in squares]
    return ans

class Puzzle:
    def __init__(self, section_map=None, puzzle_state=None, stars=None):
        if section_map is None:
            return

        section_map = section_map.split('\n')
        self.size = len(section_map)
        if puzzle_state is not None:
            puzzle_state = puzzle_state.split('\n')
        else:
            puzzle_state = ['.' * self.size for _ in range(self.size)]

        self.board = [
            [
                Tile((row, col), section_map[row][col], puzzle_state[row][col])
                for col in range(self.size)
            ] for row in range(self.size)
        ]
        self.stars = stars
        self.groups = []

    def init_groups(self):
        for row in range(self.size):
            group = []
            for col in range(self.size):
                group.append(self.board[row][col])
            self.groups.append(Group(group, self.stars))

        for col in range(self.size):
            group = []
            for row in range(self.size):
                group.append(self.board[row][col])
            self.groups.append(Group(group, self.stars))

        sections = defaultdict(list)
        for row in self.board:
            for tile in row:
                sections[tile.section].append(tile)
        
        for tiles in sections.values():
            self.groups.append(Group(tiles, self.stars))

        # for group in self.groups:
        #     print(group, get_2x2_groups(group.tiles))

    def groups_containing_tile(self, tile):
        for group in self.groups:
            if group.contains(tile):
                yield group

    # return all tiles that would be made impossible if this tile were filled in with a star
    def all_affected(self, tile):
        # all surrounding:
        ans = set()
        for row_offset in range(-1, 2):
            for col_offset in range(-1, 2):
                row = tile.row + row_offset
                col = tile.col + col_offset
                if row_offset == 0 and col_offset == 0:
                    continue
                if row >= self.size or row < 0:
                    continue
                if col >= self.size or col < 0:
                    continue
                
                ans.add(self.board[row][col])
        
        for group in self.groups_containing_tile(tile):
            if group.stars == 1:
                ans |= group.tiles

        try:
            ans.remove(tile)
        except KeyError:
            pass
        return ans

    # given list of tiles, find all groups that are clobbered if these tiles are eliminated
    def find_all_clobbering_helper(self, tiles):
        # print(tiles)
        ans = []
        for group in self.groups:
            overlap = group.get_overlap(tiles)
            left = len(group.tiles) - overlap
            if left < group.stars:
                ans.append(group)
        return ans
    
    def find_all_clobbering(self):
        for row in self.board:
            for tile in row:
                if not tile.empty():
                    continue
                for group in self.find_all_clobbering_helper(self.all_affected(tile)):
                    yield tile
                    break

    def multi_group_exclusion_helper(self, current, tile_set, remaining_groups, stars):
        current_sum = sum((group.stars for group in current))
        if current_sum == stars:
            return current
        possible_groups = []
        current_union = set()
        for group in current:
            current_union |= group.tiles

        for group in remaining_groups:
            # fits in the required stars AND is disjoint with all other current small groups AND is a subset of the big groups
            if group.stars <= stars and len(group.tiles & current_union) == 0 and group.tiles < tile_set:
                possible_groups.append(group)
        for group in possible_groups:
            remaining_groups.remove(group)
            yield from self.multi_group_exclusion_helper(current + [group], tile_set, remaining_groups, stars)
            remaining_groups.add(group)


    
    def find_multi_group_exclusions(self, depth):
        group_exclusions = []
        checks = 0
        for group_set_big in combinations(self.groups, depth):
            remaining_groups = self.groups.copy()
            for group in group_set_big:
                remaining_groups.remove(group)
            tile_set = group_union(group_set_big)
            big_group_stars = sum((group.stars for group in group_set_big))
            
            for group_set_small in combinations(remaining_groups, depth):
                small_group_stars = sum((group.stars for group in group_set_small))
                checks += 1
                if len(group_conjunction(group_set_small)) > 0:
                    continue
                if big_group_stars != small_group_stars:
                    continue
                for group2 in group_set_small:
                    if not group2.is_subset(tile_set):
                        break
                else:
                    group_set_big_copy = [group.copy() for group in group_set_big]
                    group_set_small_copy = [group.copy() for group in group_set_small]
                    group_exclusions.append((group_set_big_copy, group_set_small_copy))

        found = 0
        for big, small in group_exclusions:
            disjoint = group_union(big) ^ group_union(small)
            if len(disjoint) > 0:
                found += 1
                original_tiles_list = []
                for tile in disjoint:
                    original_tiles_list.append(self.board[tile.row][tile.col])
                self.eliminate_tiles(original_tiles_list)
        return found, checks

    def copy(self):
        puzzle = Puzzle()
        puzzle.groups = [group.copy() for group in self.groups]
        puzzle.size = self.size
        puzzle.stars = self.stars
        puzzle.board = [
            [
                self.board[row][col].copy()
                for col in range(self.size)
            ] for row in range(self.size)
        ]
        return puzzle
    
    def pretty_print(self, old_puzzle=None):
        print(' ' + string.ascii_lowercase[:self.size])
        for row in range(self.size):
            print((row + 1) % 10, end='')
            for col in range(self.size):
                section = self.board[row][col].section
                bg_color = SECTION_BGS[(ord(section) - ord('a')) % len(SECTION_BGS)]
                is_different = old_puzzle is not None and old_puzzle.board[row][col].value != self.board[row][col].value
                if is_different:
                    text_color = WHITE
                else:
                    text_color = BLACK
                
                print(f'\033[48;5;{bg_color}m', end='')
                print(f'\033[38;5;{text_color}m', end='')
                if self.board[row][col].value == 'x':
                    print(UNICODE_DOT, end='')
                elif self.board[row][col].value == '*':
                    print('&', end='')
                else:
                    #print(['x', 'o'][(row + col) % 2], end='')
                    print(' ', end='')
            print('\033[0m')
    
    def __eq__(self, other):
        return self.board == other.board and self.stars == other.stars and self.groups == other.groups

    def remove_redundant_groups(self):
        self.groups = [group for group in self.groups if not group.empty()]
        self.groups = list(set(self.groups))

    def eliminate_tiles(self, tiles):
        for group in self.groups:
            for tile in tiles:
                group.remove_tile(tile)
        
        for tile in tiles:
            tile.value = 'x'

        self.remove_redundant_groups()

    def place_stars_on_tiles(self, tiles):
        for tile in tiles:
            groups = list(self.groups_containing_tile(tile))
            to_remove = list(self.all_affected(tile)) + [tile]
            for group in groups:
                group.stars -= 1
            self.eliminate_tiles(to_remove)
            tile.value = '*'

    def place_star_solved_groups(self):
        ans = 0
        star_tiles = set()
        for group in self.groups:
            if len(group.tiles) == group.stars:
                ans += 1
                star_tiles |= group.tiles
                self.place_stars_on_tiles(group.tiles.copy())
        return len(star_tiles)

    def apply_2x2_rule(self):
        ans = 0
        to_remove = []
        for group in self.groups:
            if group.stars == 1:
                continue
            groups_2x2 = get_2x2_groups(group.tiles)
            if len(groups_2x2) == group.stars:
                ans += 1
                newgroups = [
                    Group(tiles, 1) for tiles in groups_2x2
                ]
                for g in newgroups:
                    self.groups.append(g)
                to_remove.append(group)
        for group in to_remove:
            self.groups.remove(group)
        return ans


    def solve(self):
        self.init_groups()
        old_puzzle = self.copy()
        while True:
            self.pretty_print(old_puzzle)
            input('Press Enter to step...')
            old_puzzle = self.copy()

            if len(self.groups) == 0:
                print('Puzzle is solved, stopping')
                break

            print('looking for solved groups... ', end='')
            num_solved = self.place_star_solved_groups()
            print(f'{num_solved} solved groups')
            if num_solved > 0:
                continue


            print('looking for clobbering... ', end='')
            clobbering = list(self.find_all_clobbering())
            print(f'{len(clobbering)} clobbering')
            if len(clobbering) > 0:
                self.eliminate_tiles(clobbering)
                continue

            print(f'looking for level 1 multi-group exclusions... ', end='')
            num_exclusions, checks = self.find_multi_group_exclusions(1)
            print(f'{num_exclusions} exclusions in {checks} checks')
            if num_exclusions > 0:
                continue

            print(f'looking for level 2 multi-group exclusions... ', end='')
            num_exclusions, checks = self.find_multi_group_exclusions(2)
            print(f'{num_exclusions} exclusions in {checks} checks')
            if num_exclusions > 0:
                continue

            print('Applying 2x2 rule...', end='')
            num_2x2 = self.apply_2x2_rule()
            print(f'{num_2x2} groups split')
            if num_2x2 > 0:
                print(self.groups)
                continue
            
            print("No rules to apply, giving up")
            break


def convert_task(task):
    from string import ascii_lowercase
    from math import sqrt
    nums = list(map(int, task.split(',')))
    size = round(sqrt(len(nums)))
    ans = ''
    for row in range(size):
        curr_row = ''
        for col in range(size):
            curr_row += ascii_lowercase[nums[row * size + col] - 1]
        ans += curr_row
        if row != size - 1:
            ans += '\n'

    return ans


def main():
    puzzle_name = input("Enter name of puzzle file without extension: ")
    print(f'Loading puzzle from {puzzle_name}.txt...')
    with open(puzzle_name + '.txt') as puzzle_file:
        puzzle_format = puzzle_file.readline().strip()
        stars = int(puzzle_file.readline().strip())
        if puzzle_format == 'online':
            task = puzzle_file.readline().strip()
            section_map = convert_task(task)
        elif puzzle_format == 'original':
            section_map = [puzzle_file.readline().strip()]
            remaining = len(section_map[0]) - 1
            for _ in range(remaining):
                section_map.append(puzzle_file.readline().strip())
            section_map = '\n'.join(section_map)

        puzzle = Puzzle(section_map, None, stars)
        puzzle.solve()


main()
