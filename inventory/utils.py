DAMM_OP_TABLE = [
        [0, 7, 4, 1, 6, 3, 5, 8, 9, 2],   # col 0
        [3, 0, 2, 7, 1, 6, 8, 9, 4, 5],   # col 1
        [1, 9, 0, 5, 2, 7, 6, 4, 3, 8],   # col 2
        [7, 2, 6, 0, 3, 4, 9, 5, 8, 1],   # col 3
        [5, 1, 8, 9, 0, 2, 7, 3, 6, 4],   # col 4
        [9, 5, 7, 8, 4, 0, 2, 6, 1, 3],   # col 5
        [8, 4, 1, 3, 5, 9, 0, 2, 7, 6],   # col 6
        [6, 8, 3, 4, 9, 5, 1, 0, 2, 7],   # col 7
        [4, 6, 5, 2, 7, 8, 3, 1, 0, 9],   # col 8
        [2, 3, 9, 6, 8, 1, 4, 7, 5, 0],   # col 9
    ]


def check_digit(digitstring):
    """An implementation of the Damm algorithm."""
    if not digitstring.isdecimal():
        return -1
    interim = 0

    for digit in digitstring:
        cx = int(digit)
        rx = interim
        interim = DAMM_OP_TABLE[cx][rx]
    return interim
