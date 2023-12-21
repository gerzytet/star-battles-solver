import itertools
import math
import string
from collections import defaultdict
import multi_group_exclusion
import rules_2x2
from group import Group

# Colors & Symbols for grid
import utils
from chain_reactions import apply_chains
from tile import Tile

SECTION_BGS = [
    40, 191, 218, 172, 63, 226, 45, 105, 249, 188
]
BLACK = 232
WHITE = 196
UNICODE_STAR = "★"
UNICODE_DOT = "·"
UNICODE_SQUARE = '■'

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
                Tile((row, col), section_map[row][col], puzzle_state[row][col], self.size)
                for col in range(self.size)
            ] for row in range(self.size)
        ]
        self.stars = stars
        self.groups = []
        self.all_groups = set()

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

        for group in self.groups:
            print(group, group.bits)

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

    def print_groups(self, groups):
        groups = list(groups)
        print(' ' + string.ascii_lowercase[:self.size])
        for row in range(self.size):
            print((row + 1) % 10, end='')
            for col in range(self.size):
                text_color = WHITE
                owner = None
                for i in range(len(groups)):
                    group = groups[i]
                    if group.contains(self.board[row][col]):
                        bg_color = SECTION_BGS[i % len(SECTION_BGS)]
                        owner = group
                        break
                else:
                    bg_color = BLACK

                print(f'\033[48;5;{bg_color}m', end='')
                print(f'\033[38;5;{text_color}m', end='')
                print(owner.stars % 10 if owner else ' ', end='')
            print('\033[0m')

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
                    # print(['x', 'o'][(row + col) % 2], end='')
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
                group.remove(tile)

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
        return star_tiles

    def apply_2x2_rule(self):
        ans = 0
        to_remove = []
        for group in self.groups:
            if group.stars == 1:
                continue
            groups_2x2 = rules_2x2.get_2x2_groups(group.tiles)
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

    def check_solution_validity(self):
        section_stars = {string.ascii_lowercase[i]: 0 for i in range(self.size)}
        row_stars = {r: 0 for r in range(self.size)}
        col_stars = row_stars.copy()
        for row in self.board:
            for tile in row:
                if tile.empty():
                    return False
                elif tile.value == 'x':
                    continue
                section_stars[tile.section] += 1
                row_stars[tile.row] += 1
                col_stars[tile.col] += 1

        for v in itertools.chain(section_stars.values(), row_stars.values(), col_stars.values()):
            if v != self.stars:
                return False

        # TODO: make sure no stars touch
        return True

    def check_validity(self):
        section_stars = {string.ascii_lowercase[i]: 0 for i in range(self.size)}
        row_stars = {r: 0 for r in range(self.size)}
        col_stars = row_stars.copy()
        for row in self.board:
            for tile in row:
                if tile.value == '*':
                    section_stars[tile.section] += 1
                    row_stars[tile.row] += 1
                    col_stars[tile.col] += 1

        #for v in itertools.chain(section_stars.values(), row_stars.values(), col_stars.values()):
        #    if v > self.stars:
        #        return False

        for section in section_stars:
            if section_stars[section] > self.stars:
                bg_color = SECTION_BGS[(ord(section) - ord('a')) % len(SECTION_BGS)]
                return False, f'Too many stars in section \033[48;5;{bg_color}m{section}\033[0m'

        for row in range(self.size):
            if row_stars[row] > self.stars:
                return False, f'Too many stars in row {row + 1}'

        for col in range(self.size):
            if row_stars[col] > self.stars:
                return False, f'Too many stars in column {col + 1}'

        for group in self.groups:
            if rules_2x2.get_num_2x2(group.tiles, group.bits) < group.stars:
                #if group.is_row():
                #    return False, f'{group.row_number()}'
                return False, f'Not enough room for stars in group {group}'

        return True, 'Flase eggrt gkole'

    def update_all_groups(self):
        for group in self.groups:
            self.all_groups.add(group.copy())

    def solve(self):
        self.init_groups()
        old_puzzle = self.copy()
        while True:
            self.pretty_print(old_puzzle)
            self.remove_redundant_groups()
            self.update_all_groups()
            input('Press Enter to step...')
            old_puzzle = self.copy()

            #print(f'Validity: {self.check_validity()[0]}')

            if len(self.groups) == 0:
                print('Puzzle is solved with a' + (
                    'n invalid' if not self.check_solution_validity() else ' valid') + ' solution')
                break

            print('looking for solved groups... ', end='')
            num_solved = len(self.place_star_solved_groups())
            print(f'{num_solved} solved groups')
            if num_solved > 0:
                continue

            print('looking for 2x2 clobbering... ', end='')
            clobbering = list(rules_2x2.find_all_2x2_clobbering(self))
            print(f'{len(clobbering)} clobbering')
            if len(clobbering) > 0:
                self.eliminate_tiles(clobbering)
                continue

            print('Applying 2x2 rule...', end='')
            num_2x2 = self.apply_2x2_rule()
            print(f'{num_2x2} groups split')
            if num_2x2 > 0:
                print(self.groups)
                continue

            print('Looking for chain reactions...', end='')
            result = apply_chains(self)
            if result:
                print('Chain found!')
                continue

            found_exclusion = False
            total_checks = 0
            curr_checks = 1
            level = 1
            best_value = math.inf
            best_disjoint = None
            best_stars = None
            best_big = None
            while curr_checks > 0:
                print(f'looking for common level {level} multi-group exclusions... ', end='')
                curr_checks = 0
                stars, disjoint, big, checks = multi_group_exclusion.find_multi_group_exclusions(level, self, common=True, use_2x2=True)
                curr_checks += checks
                if stars == 0:
                    print(f'found exclusion in {total_checks} checks')
                    found_exclusion = True
                    print(stars, disjoint, big)
                    multi_group_exclusion.apply_exclusion_result(self, stars, disjoint, big)
                    break

                stars, disjoint, big, checks = multi_group_exclusion.find_multi_group_exclusions(level, self, common=True, next_best_thing=True)
                if stars is not None:
                    value = len(disjoint) - stars
                    if value < best_value:
                        best_value = value
                        best_disjoint = disjoint
                        best_big = big
                        best_stars = stars
                curr_checks += checks
                level += 1
                print(f'{curr_checks} checks')
                total_checks += curr_checks

            if found_exclusion:
                continue
            if best_disjoint is not None:
                print(f'going with next best: {best_stars} stars in {len(best_disjoint)}-tile group')
                print(best_stars, best_disjoint, best_big)
                self.print_groups([Group(best_disjoint, best_stars)])
                multi_group_exclusion.apply_exclusion_result(self, best_stars, best_disjoint, best_big)
                continue

            #found = False
            #for level in range(1, self.size):
            #    print(f'looking for uncommon level {level} multi-group exclusions... ', end='')
            #    num_exclusions, checks = multi_group_exclusion.find_multi_group_exclusions(level, self)
            #    print(f'{num_exclusions} exclusions in {checks} checks')
            #    if num_exclusions > 0:
            #        found = True
            #        break
            #if found:
            #    continue

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
    with open(f'puzzles/{puzzle_name}.txt') as puzzle_file:
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
print(f'{len(rules_2x2.cache_2x2.keys())} keys in 2x2 cache')
