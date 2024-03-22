import board
import usb_cdc
from kmk.kmk_keyboard import KMKKeyboard as _KMKKeyboard
from kmk.modules.split import Split, SplitType, SplitSide
from kmk.scanners import DiodeOrientation
from storage import getmount

side = SplitSide.LEFT if str(getmount('/').label)[-1] == 'L' else SplitSide.RIGHT

if side == SplitSide.LEFT:
    print("Host board is LEFT")

else:
    print("Host board is RIGHT")

class KMKKeyboard(_KMKKeyboard):
    # Left side pin map (not symmetrical)
    if side == SplitSide.LEFT:
        col_pins = (
            board.A3,    #C0
            board.A2,    #C1
            board.A1,    #C2
            board.A0,    #C3
            board.CLK,   #C4
            board.MISO,  #C5
            board.MOSI,  #C6
        )
        row_pins = (
            board.D9,    #R0
            board.D8,    #R1
            board.D7,    #R2
            board.D6,    #R3
            board.D5,    #R4
            board.D4,    #R5
        )

    # Right side pin map (not symmetrical)
    else:
        col_pins = (
            # The pins on the right side are all off by one - this also changes where
            #   the encoder pins end up
            board.D10,   #C7  (0)
            board.MOSI,  #C8  (1)
            board.MISO,  #C9  (2)
            board.CLK,   #C10 (3)
            board.A0,    #C11 (4)
            board.A1,    #C12 (5)
            board.A2,    #C13 (6)

        )
        row_pins = (
            board.D4,    #R0
            board.D5,    #R1
            board.D6,    #R2
            board.D7,    #R3
            board.D8,    #R4
            board.D9,    #R5
        )



    diode_orientation = DiodeOrientation.COL2ROW
    # flake8: noqa
    # fmt: off
    # Several slots are "empty" in the actual matrix wiring (by the knobs)
    #   0, 1, 6, 48, 43, 42
    coord_mapping = [
        0,  1,  2,  3,  4,  5,   6,                48, 47, 46, 45, 44, 43, 42,
        7,  8,  9,  10, 11, 12, 13,                55, 54, 53, 52, 51, 50, 49,
        14, 15, 16, 17, 18, 19, 20,                62, 61, 60, 59, 58, 57, 56,
        21, 22, 23, 24, 25, 26,                        68, 67, 66, 65, 64, 63,
        28, 29, 30, 31, 32, 33, 34, 27,        69, 76, 75, 74, 73, 72, 71, 70,
        35, 36, 37, 38,   39,   40, 41,        83, 82,   81,   80, 79, 78, 77,
    ]
