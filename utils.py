def bits_from_tiles(tiles):
    bits = 0
    for tile in tiles:
        bits |= tile.bit
    return bits
