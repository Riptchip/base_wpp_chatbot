# Code got from https://gist.github.com/bryanhelmig/2cc72b92e5d3c6afd71ed86c8247a4f8
import itertools
import math

def tokenize_keyboard(board):
    return [list(row.strip()) for row in board]

def invert_grid(grid):
    out = {}
    for row_i, row in enumerate(grid):
        for col_i, cell in enumerate(row):
            if cell:
                out[cell] = (float(row_i), float(col_i))
    return out

KEYBOARD = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'],
    ['',  '',  '',  '',  ' ',  '',  '',  '',  '',  ''],
]
KEYBOARD_GRID = invert_grid(KEYBOARD)

SHIFTED_KEYBOARD = [
    ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+'],
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '|'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"'],
    ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?'],
    ['',  '',  '',  '',  ' ',  '',  '',  '',  '',  ''],
]
SHIFTED_KEYBOARD_GRID = invert_grid(SHIFTED_KEYBOARD)

def get_distance(a, b):
    distance = 0
    
    a_keyboard_pos = KEYBOARD_GRID.get(a)
    a_shifted_keyboard_pos = SHIFTED_KEYBOARD_GRID.get(a)
    b_keyboard_pos = KEYBOARD_GRID.get(b)
    b_shifted_keyboard_pos = SHIFTED_KEYBOARD_GRID.get(b)
    if (not (a_keyboard_pos and b_keyboard_pos)) and (not (a_shifted_keyboard_pos and b_shifted_keyboard_pos)):
        distance += 3
    
    a_pos = a_keyboard_pos or a_shifted_keyboard_pos
    b_pos = b_keyboard_pos or b_shifted_keyboard_pos
    if a_pos and b_pos:
        return distance + math.hypot(a_pos[0] - b_pos[0], a_pos[1] - b_pos[1])
    return distance + 4

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def score_not_mashing(text):
    "Returns a float - higher score is less likely to be mashing."
    distance = 0.0
    for a, b in pairwise(text):
        distance += (get_distance(a, b) - 1)
    return distance / len(text)

def is_mashing(text, cutoff=2.15):
    return score_not_mashing(text) < cutoff
