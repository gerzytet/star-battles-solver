import rules_2x2
from group import Group

def test_for_chain(puzzle, tile):
    p = puzzle.copy()
    p.groups.append(
        Group({p.board[tile.row][tile.col]}, 1)
    )

    length = 0
    while True:
        length += 1
        if not p.check_validity()[0]:
            p.pretty_print()
            return length

        num_solved = len(p.place_star_solved_groups())
        if num_solved > 0:
            continue

        #clobbering = list(rules_2x2.find_all_2x2_clobbering(p))
        #if len(clobbering) > 0:
        #    p.eliminate_tiles(clobbering)
        #    continue

        return -1

def apply_chains(puzzle):
    solutions = []
    for row in puzzle.board:
        for tile in row:
            if not tile.empty():
                continue
            if (length := test_for_chain(puzzle, tile)) != -1:
                solutions.append((length, tile))
    if len(solutions) > 0:
        _, tile = min(solutions, key=lambda s: s[0])
        puzzle.eliminate_tiles([tile])
        return True
    return False