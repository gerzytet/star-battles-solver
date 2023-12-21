import string


class Tile:
    #
    def __init__(self, pos, section, value, size):
        if isinstance(pos, tuple):
            self.row, self.col = pos
        else:
            raise ValueError('pos is not a tuple')

        self.section = section
        self._value = value
        self.hash = None
        self.update_hash()
        self.bit = 1 << (self.col + self.row * size)
        self.size = size

    def __str__(self):
        return str(self.row + 1) + string.ascii_uppercase[self.col]

    def __eq__(self, other):
        return (
                self.row == other.row and
                self.col == other.col and
                self.value == other.value and
                self.section == other.section
        )

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.update_hash()

    def update_hash(self):
        self.hash = hash((self.row, self.col, self.value, self.section))

    def __hash__(self):
        return self.hash

    __repr__ = __str__

    def copy(self):
        return Tile((self.row, self.col), self.section, self.value, self.size)

    def empty(self):
        return self.value == '.'
