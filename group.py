import utils

class Group:
    def __init__(self, tiles, stars):
        self.tiles = set(tiles)
        self.stars = stars
        self.bits = utils.bits_from_tiles(self.tiles)

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

    def remove(self, tile):
        try:
            self.tiles.remove(tile)
        except KeyError:
            pass
        self.bits &= ~tile.bit

    def add(self, tile):
        self.tiles.add(tile)
        self.bits |= tile.bit

    def __hash__(self):
        return hash(self.bits)

    def __repr__(self):
        return f'Group({self.tiles}, {self.stars})'

    def empty(self):
        return len(self.tiles) == 0 and self.stars == 0

    def contains(self, tile):
        return tile in self.tiles

    def is_row(self):
        row = None
        for tile in self.tiles:
            if row is None:
                row = tile.row
            elif row != tile.row:
                return False
        return True

    def is_col(self):
        col = None
        for tile in self.tiles:
            if col is None:
                col = tile.col
            elif col != tile.col:
                return False
        return True

    def row_number(self):
        return next(iter(self.tiles)).row

    def col_number(self):
        return next(iter(self.tiles)).col