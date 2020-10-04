import os
import math

def image_path(rel):
    return os.path.join("images", rel)

def rooms_path(rel):
    return os.path.join("rooms", rel)

def fonts_path(rel):
    return os.path.join("fonts", rel)

def sounds_path(rel):
    return os.path.join("sounds", rel)

def mag(*args):
    """ Magnitude of any number of axes """
    n = len(args)
    return (sum([abs(arg)**2 for arg in args]))**(1/2)

def approach(num, dest, amt):
    d = dest - num
    num += amt
    if amt > 0:
        if num > dest:
            num = dest
    elif amt < 0:
        if num < dest:
            num = dest
    return num


MAX_FPS = 64

TILE_SIZE = 48

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)

FAST_SPINNING=1
SLIPPERY_SOCKS=2
DOUBLE_SHOT=3
BOUNCY=4
FAST_SHOOTING=5
