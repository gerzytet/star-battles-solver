import itertools
import math
from itertools import combinations, chain
import rules_2x2
from group import Group

checks = 0
considered = 0


def multi_group_exclusion_helper(puzzle, current, tile_set, tile_set_bits, remaining_groups, stars, current_stars,
                                 current_union, current_union_bits, use_2x2=False, next_best_thing=False):
    global checks
    if current_stars == stars:
        return None, None

    # eliminate all small groups touching existing small groups
    to_remove = []
    for group in remaining_groups:
        if group.bits & current_union_bits != 0:
            to_remove.append(group)
        elif not use_2x2 and group.bits & tile_set_bits != group.bits:
            to_remove.append(group)
    for group in to_remove:
        remaining_groups.remove(group)

    best_value = math.inf
    best_stars_out = None
    best_tiles_out = None
    for group in remaining_groups.copy():
        if group.stars > stars:
            continue
        checks += 1

        if use_2x2:
            disjoint = group.tiles - tile_set
            disjoint_bits = group.bits ^ (group.bits & tile_set_bits)
            num_2x2 = rules_2x2.get_num_2x2(disjoint, disjoint_bits)
            stars_in = max(0, group.stars - num_2x2)
            if stars_in == 0:
                continue
        else:
            stars_in = group.stars

        current_union |= group.tiles

        total_stars_in = current_stars + stars_in
        stars_out = stars - total_stars_in
        tiles_out = tile_set - current_union
        value = len(tiles_out) - stars_out
        if ((next_best_thing and value < best_value) or stars_out == 0) and tiles_out != set() and Group(tiles_out, stars_out) not in puzzle.all_groups:
            best_value = value
            best_stars_out = stars_out
            best_tiles_out = tiles_out

        remaining_groups.remove(group)
        to_remove.append(group)
        stars_out, tiles_out = multi_group_exclusion_helper(puzzle, current + [group], tile_set, tile_set_bits,
                                                            remaining_groups,
                                                            stars,
                                                            total_stars_in, current_union,
                                                            current_union_bits | group.bits)
        if stars_out is not None and tiles_out is not None:
            value = len(tiles_out) - stars_out
            if value < best_value:
                best_value = value
                best_stars_out = stars_out
                best_tiles_out = tiles_out

        current_union -= group.tiles

    for group in to_remove:
        remaining_groups.add(group)

    return best_stars_out, best_tiles_out


def group_union(groups):
    ans = set()
    for group in groups:
        ans |= group.tiles
    return ans


def generate_all_big_groups(groups, depth, remaining_groups):
    for groups in combinations(groups, depth):
        for group in groups:
            remaining_groups.remove(group)
        yield groups
        for group in groups:
            remaining_groups.add(group)


def generate_row_combinations(buckets, depth, last_was_zero, pos):
    if pos >= len(buckets):
        return
    if depth == 0:
        return
    if last_was_zero:
        start = 0
    else:
        start = 1
    for i in range(start, len(buckets[pos]) + 1):
        if depth == i:
            yield from combinations(buckets[pos], i)
        else:
            yield from itertools.starmap(itertools.chain, itertools.product(combinations(buckets[pos], i),
                                                                            generate_row_combinations(buckets,
                                                                                                      depth - i, i == 0,
                                                                                                      pos + 1)))


def generate_common_big_groups(groups, depth, remaining_groups):
    rows = set()
    cols = set()
    sections = set()
    for group in groups:
        if group.is_row():
            rows.add(group)
        elif group.is_col():
            cols.add(group)
        else:
            sections.add(group)

    num_rows = max(map(lambda x: x.row_number(), groups)) + 1
    num_cols = max(map(lambda x: x.col_number(), groups)) + 1
    row_buckets = [[] for _ in range(num_rows)]
    col_buckets = [[] for _ in range(num_cols)]
    for row in rows:
        row_buckets[row.row_number()].append(row)
    for col in cols:
        col_buckets[col.col_number()].append(col)

    # rows on sections
    remaining_groups -= cols
    remaining_groups -= rows
    # yield from combinations(rows, depth)
    yield from generate_row_combinations(row_buckets, depth, True, 0)
    remaining_groups |= cols
    remaining_groups |= rows

    # cols on sections
    remaining_groups -= rows
    remaining_groups -= cols
    yield from generate_row_combinations(col_buckets, depth, True, 0)
    remaining_groups |= rows
    remaining_groups |= cols

    # sections on rows
    remaining_groups -= cols
    remaining_groups -= sections
    yield from combinations(sections, depth)
    remaining_groups |= cols
    remaining_groups |= sections

    # sections on cols
    remaining_groups -= rows
    remaining_groups -= sections
    yield from combinations(sections, depth)
    remaining_groups |= rows
    remaining_groups |= sections


def find_multi_group_exclusions(depth, puzzle, common=False, use_2x2=False, next_best_thing=False):
    global checks
    checks = 0

    remaining_groups = set(puzzle.groups.copy())
    if common:
        big_groups = generate_common_big_groups(puzzle.groups, depth, remaining_groups)
    else:
        big_groups = generate_all_big_groups(puzzle.groups, depth, remaining_groups)

    best_value = math.inf
    best_stars = None
    best_tiles = None
    best_big_group = None
    for group_set_big in map(list, big_groups):
        tile_set_bits = 0
        tile_set = set()
        overlapping = False
        for group in group_set_big:
            if tile_set_bits & group.bits != 0:
                overlapping = True
                break
            tile_set_bits |= group.bits
            tile_set |= group.tiles
        #TODO: don't generate overlapping groups in the first place
        if overlapping:
            continue
        big_group_stars = sum((group.stars for group in group_set_big))

        to_remove = []
        for group in remaining_groups:
            if group.bits & tile_set_bits == 0:
                to_remove.append(group)
        for group in to_remove:
            remaining_groups.remove(group)

        stars, tiles = multi_group_exclusion_helper(puzzle, [], tile_set, tile_set_bits, remaining_groups.copy(),
                                                    big_group_stars, 0, set(), 0, use_2x2, next_best_thing)
        if stars is not None and tiles is not None:
            value = len(tiles) - stars
            if value < best_value:
                best_value = value
                best_stars = stars
                best_tiles = tiles
                best_big_group = group_set_big

        for group in to_remove:
            remaining_groups.add(group)

    # found = 0
    # for big, small in group_exclusions:
    #    disjoint = group_union(big) - group_union(small)
    #    if len(disjoint) > 0:
    #        found += 1
    #        print(big, small)
    #        original_tiles_list = []
    #        for tile in disjoint:
    #            original_tiles_list.append(puzzle.board[tile.row][tile.col])
    #        puzzle.eliminate_tiles(original_tiles_list)
    return best_stars, best_tiles, best_big_group, checks

def apply_exclusion_result(puzzle, stars, disjoint, big):
    if stars == 0:
        puzzle.eliminate_tiles(disjoint)
        return

    #for group in big:
    #    if disjoint & group.tiles == disjoint:
    #        for tile in disjoint:
    #            group.remove(tile)
    #            group.stars -= stars

    puzzle.groups.append(
        Group(disjoint, stars)
    )