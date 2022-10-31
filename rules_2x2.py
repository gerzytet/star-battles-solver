import utils

cache_2x2 = {}
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

def find_all_2x2_clobbering_helper(puzzle, tiles):
    # print(tiles)
    ans = []
    tiles_bits = utils.bits_from_tiles(tiles)
    for group in puzzle.groups:
        disjoint = group.tiles - tiles
        disjoint_bits = group.bits ^ (group.bits & tiles_bits)
        num_2x2 = get_num_2x2(disjoint, disjoint_bits)
        if num_2x2 < group.stars:
            ans.append(group)
    return ans

def find_all_2x2_clobbering(puzzle):
    for row in puzzle.board:
        for tile in row:
            if not tile.empty():
                continue
            for group in find_all_2x2_clobbering_helper(puzzle, puzzle.all_affected(tile)):
                yield tile
                break

def get_num_2x2(tiles, bits):
    if bits in cache_2x2:
        return cache_2x2[bits]
    ans = len(get_2x2_groups(tiles))
    cache_2x2[bits] = ans
    return ans

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
