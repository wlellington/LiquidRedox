# Write your code here :-)
print("Starting...")
# Micropython stuff
import board
import usb_cdc
import supervisor
import storage
from storage import getmount

# KMK imports
from kmk.consts import UnicodeMode
from kb import KMKKeyboard
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.modules.tapdance import TapDance
from kmk.modules.mouse_keys import MouseKeys
from kmk.modules.dynamic_sequences import DynamicSequences
from kmk.modules.split import SplitType, SplitSide
from kmk.extensions.rgb import AnimationModes
from kmk.extensions.media_keys import MediaKeys
from kmk.modules.combos import Combos, Sequence
from kmk.handlers.sequences import simple_key_sequence
from kmk.handlers.sequences import send_string

# Custom UART Stuff
from uart_split import Split,
from uart_lock_status import LockStatus
from uart_encoder import EncoderHandler
from status_led import RGB
from status_led import LEDStatus
from status_led import CustomColors as CC

# Check if serial was connected (boot.py settings)
console = usb_cdc.console
print("Console is: ", console)

# Determine side to customize setup
side = SplitSide.LEFT if str(getmount('/').label)[-1] == 'L' else SplitSide.RIGHT

# Custom Split Keyboard object settings
split = Split(
    split_flip=False,  # If both halves are the same, but flipped, set this True
    split_side=None,  # Sets if this is to SplitSide.LEFT or SplitSide.RIGHT, or use EE hands
    split_type=SplitType.UART,  # Defaults to UART
    uart_interval=20,  # Sets the uarts delay. Lower numbers draw more power
    data_pin=board.RX,  # The primary data pin to talk to the secondary device with
    data_pin2=board.TX,  # Second uart pin to allow 2 way communication
    uart_flip=False,  # Reverses the RX and TX pins if both are provided
    #use_pio=False,  # Use RP2040 PIO implementation of UART. Required if you want to use other pins than RX/TX
)

# Create + configure keyboard
keyboard = KMKKeyboard()
if console is None:
    print("Disabling debug! (Though you shouldnt be able to see this...)")
    keyboard.debug_enabled = False

# Set up KMK Modules
keyboard.modules.append(split)
layers = Layers()
keyboard.modules.append(layers)
tapdance = TapDance()
tapdance.tap_time = 50
keyboard.modules.append(tapdance)
media_keys = MediaKeys()
keyboard.extensions.append(media_keys)
mouse_keys = MouseKeys()
keyboard.modules.append(mouse_keys)

# Custom UART Overwrites
encoder_handler = EncoderHandler(
                        split=split
                        )
keyboard.modules.append(encoder_handler)
lock_status = LockStatus(
                        split=split
                        )
keyboard.extensions.append(lock_status)

# Back to normal modules
dynamic_sequences = DynamicSequences(
                                    slots = 5,
                                    key_interval=10,
                                    )
keyboard.modules.append(dynamic_sequences)
combos = Combos()
keyboard.modules.append(combos)


# Side specific settings
if side == SplitSide.LEFT:
    # Encoder stuff
    encoder_handler.pins = (
        (board.D2, board.D3, board.D10,), # encoder #1
        (None, None, None,), # encoder #2 nulled out since its on the other board
        )

    # LEDStatus Stuff (no num lock or macros on left)
    num_lock_leds = []
    macro_leds = []

else:
    # Encoder stuff
    encoder_handler.pins = (
        (None, None, None,), # encoder #1 nulled out since its on the other board
        (board.D2, board.D3, board.A3,), # encoder #2
        )

     # LEDStatus Stuff
    num_lock_leds = [4]
    macro_leds = [4, 3, 2, 1]

# Custom RGB overwrite object settings
rgb = RGB(pixel_pin=board.SDA,
        num_pixels=5,
        val_default=20,
        val_limit=100,
        val_step=4,
        sat_default=255,
        hue_default=CC.PRICKLY[0],
        rgb_order=(1, 0, 2, 3),  # g r b W
        animation_mode=AnimationModes.STATIC,
        refresh_rate=10,
        )
keyboard.extensions.append(rgb)

# Custom LEDStatus lightving settings
#   Not based on kmk statusLED by the way
led_status = LEDStatus(
                    keyboard=keyboard,
                    rgb=rgb,
                    layers=layers,
                    layer_leds=[1,2,3,4],
                    layer_colors=[CC.PRICKLY, CC.AMBER, CC.DEEP, CC.DRIFT],
                    locks=lock_status,
                    caps_lock_leds=[0],
                    num_lock_leds=num_lock_leds,
                    dynamic_sequences = dynamic_sequences,
                    macro_leds=macro_leds,
                    sleep_minutes = 15,
                    sleep_leds = [0,1,2,3,4],
                    )
keyboard.extensions.append(led_status)

##### Dyanamic Macros Handling #####
keyboard.hidden_state = {}
keyboard.hidden_state["start_record"] = False
keyboard.hidden_state["recording"] = False
keyboard.hidden_state["target_slot"] = 0

# Set current recording state from "initiator" key
def configure_dynamic(self, keyboard, *args, **kwargs):
    keyboard.hidden_state["target_slot"] = 0
    if keyboard.hidden_state["recording"] or keyboard.hidden_state["start_record"]:
        dynamic_sequences.stop_sequence(keyboard, 1)
        dynamic_sequences.stop_sequence(keyboard, 2)
        dynamic_sequences.stop_sequence(keyboard, 3)
        dynamic_sequences.stop_sequence(keyboard, 4)
        #print("Stopping recording from config button")
        keyboard.hidden_state["recording"] = False
        keyboard.hidden_state["start_record"] = False
    else:
        if keyboard.hidden_state["start_record"] == False:
            #print("Entering Recording Selection Mode")
            keyboard.hidden_state["start_record"] = True
        else:
            keyboard.hidden_state["start_record"] = False
            keyboard.hidden_state["recording"] = False

# Select target slot for recording or playback
def target_slot(self, keyboard, target_slot, *args, **kwargs):
    #keyboard.tap_key(KC.SET_SEQUENCE(target_slot))
    if keyboard.hidden_state["start_record"]:
        #print("Recording on: ", target_slot)
        dynamic_sequences.record_sequence(keyboard, target_slot)
        keyboard.hidden_state["start_record"] = False
        keyboard.hidden_state["recording"] = True
    else:
        if keyboard.hidden_state["recording"]:
            #print("Saved to: ", target_slot)
            dynamic_sequences.stop_sequence(keyboard, target_slot)
            keyboard.hidden_state["recording"] = False
        else:
            #print("Playing from: ", target_slot)
            dynamic_sequences.play_sequence(keyboard, target_slot)

# Slot specific handlers
def target_slot_1(self, keyboard, *args, **kwargs):
    target_slot(self, keyboard, 1, *args, **kwargs)

def target_slot_2(self, keyboard, *args, **kwargs):
    target_slot(self, keyboard, 2, *args, **kwargs)

def target_slot_3(self, keyboard, *args, **kwargs):
    target_slot(self, keyboard, 3, *args, **kwargs)

def target_slot_4(self, keyboard, *args, **kwargs):
    target_slot(self, keyboard, 4, *args, **kwargs)

# Keys for keymap
RECORD = KC.NO.clone()
RECORD.after_press_handler(configure_dynamic)

R_1 = KC.NO.clone()
R_1.after_press_handler(target_slot_1)

R_2 = KC.NO.clone()
R_2.after_press_handler(target_slot_2)

R_3 = KC.NO.clone()
R_3.after_press_handler(target_slot_3)

R_4 = KC.NO.clone()
R_4.after_press_handler(target_slot_4)

### Other Macros + Sequences ###

# Board reset handler for reset key
def restart(self, keyboard, *args, **kwargs):
    print("Resetting...")
    supervisor.reload()

S_RST = KC.NO.clone()
S_RST.after_press_handler(restart)

# Keep awake macro
move_mouse = simple_key_sequence(
    (
        KC.MS_UP,
        KC.MACRO_SLEEP_MS(250),
        KC.MS_RT,
        KC.MACRO_SLEEP_MS(250),
        KC.MS_DN,
        KC.MACRO_SLEEP_MS(250),
        KC.MS_LT,
        KC.MACRO_SLEEP_MS(250),
    )
)


EMOJI = KC.LGUI(KC.DOT)

# Open windows clock app
CLOCK = simple_key_sequence(
    (
        KC.LGUI,
        KC.MACRO_SLEEP_MS(50),
        send_string("clock"),
        KC.MACRO_SLEEP_MS(50),
        KC.ENT,
    )
)

# Open windows calculator app
CALC  = simple_key_sequence(
    (
        KC.LGUI,
        KC.MACRO_SLEEP_MS(100),
        send_string("calculator"),
        KC.MACRO_SLEEP_MS(100),
        KC.ENT,
    )
)

# Open windows apps tapdance
WINAPP = KC.TD(
    CLOCK,
    CALC,
    tap_time = 200,
)

TASK = KC.LGUI(KC.TAB)

# Powertoys "always on top" macro
ATOP = simple_key_sequence(
    (
        KC.LGUI(no_release=True),
        KC.LCTL(no_release=True),
        KC.MACRO_SLEEP_MS(50),
        KC.T,
        KC.MACRO_SLEEP_MS(50),
        KC.LGUI(no_press=True),
        KC.LCTL(no_press=True),
    )
)

# Window management stuff
MANAGE = KC.TD(
    ATOP,
    TASK,
    tap_time = 200,
)

# Control sequences
CALTDEL = KC.LCTL(KC.LALT(KC.DEL))
CSHFESC = KC.LCTL(KC.LSFT(KC.ESC))

# Control tapdance
CTRLMC = KC.TD(
    CSHFESC,
    CALTDEL,
    tap_time = 200,
)

# LShift + Capslock tapdance
CAP_TDL = KC.TD(
    #KC.HT(KC.LSFT, KC.LSFT, prefer_hold = True, tap_time = 80),
    KC.LSFT,
    KC.CAPSLOCK,
    tap_time = 250,
    #prefer_hold = True,
)

# RShift + Capslock tapdance
CAP_TDR = KC.TD(
    #KC.HT(KC.LSFT, KC.LSFT, prefer_hold = True, tap_time = 80),
    KC.RSFT,
    KC.CAPSLOCK,
    tap_time = 250,
    #prefer_hold = True,
)

# Zoom in for encoder
ZOOM_IN = simple_key_sequence(
    (
        KC.LCTL(no_release=True),
        KC.MACRO_SLEEP_MS(30),
        KC.MW_UP,
        KC.MACRO_SLEEP_MS(30),
        KC.LCTL(no_press=True),
    )
)

# Zoom out for encoder
ZOOM_OUT = simple_key_sequence(
    (
        KC.LCTL(no_release=True),
        KC.MACRO_SLEEP_MS(30),
        KC.MW_DN,
        KC.MACRO_SLEEP_MS(30),
        KC.LCTL(no_press=True),
    )
)

# No key
XXXXXX = KC.NO

# Transparent key
______ = KC.TRNS

# Short keynames for mouse keys
M_4 = KC.MB_BTN4.clone()
M_5 = KC.MB_BTN5.clone()

##### Keymaps #####

# Encoder
encoder_handler.map = [
        (
            (KC.VOLD, KC.VOLU, KC.MUTE), # Volume stuff
            (KC.LCTL(KC.MINS), KC.LCTL(KC.EQL), KC.LCTL(KC.N0)), #Zoom stuff
        ), #QWERTY LAYER
        (
            (KC.TRNS, KC.TRNS, KC.TRNS),
            (KC.TRNS, KC.TRNS, KC.TRNS),
        ), #NAV LAYER
        (
            (KC.RGB_VAD, KC.RGB_VAI, KC.RGB_TOG), # RGB brightness stuff
            (KC.TRNS, KC.TRNS, KC.TRNS),
        ), #NUMPAD LAYER
        (
            (KC.VOLD, KC.VOLU, KC.MUTE), # Volume stuff
            (KC.TRNS, KC.TRNS, KC.TRNS),
        ), #Gaming LAYER
    ]

# keyboard
keyboard.keymap = [
    [   # QWERTY
        XXXXXX,  XXXXXX,  M_4,     M_5,     KC.PSCR, WINAPP,  XXXXXX,                          XXXXXX,    R_1,     R_2,     R_3,     R_4,    XXXXXX,  XXXXXX,
        KC.ESC,  KC.N1,   KC.N2,   KC.N3,   KC.N4,   KC.N5,   KC.MO(2),                        RECORD,  KC.N6,   KC.N7,   KC.N8,    KC.N9,   KC.N0,   KC.LBRC,
        KC.GRV,  KC.Q,    KC.W,    KC.E,    KC.R,    KC.T,    CTRLMC,                          KC.BSLS,  KC.Y,    KC.U,    KC.I,    KC.O,    KC.P,    KC.RBRC,
        KC.TAB,  KC.A,    KC.S,    KC.D,    KC.F,    KC.G,                                               KC.H,    KC.J,    KC.K,    KC.L,    KC.SCLN, KC.QUOT,
        CAP_TDL, KC.Z,    KC.X,    KC.C,    KC.V,    KC.B,    KC.INS, KC.DEL,        KC.MINS,  KC.EQL,   KC.N,    KC.M,    KC.COMM, KC.DOT,  KC.SLSH, CAP_TDR,
        KC.LCTL, KC.LGUI, MANAGE,  EMOJI,      KC.LALT,       KC.SPC, KC.BSPC,       KC.ENT,   KC.SPC,      KC.MO(1),      KC.LEFT, KC.UP,   KC.DOWN, KC.RGHT,
    ],
    [   # Navigation + Function
        XXXXXX,  XXXXXX, KC.MPRV, KC.MNXT,  ______,   KC.MPLY,  XXXXXX,                        XXXXXX,   ______,  ______,  ______,  ______,   XXXXXX,  XXXXXX,
        XXXXXX,  KC.F1,   KC.F2,   KC.F3,   KC.F4,    KC.F5,    KC.TG(3),                        ______,   KC.F6,   KC.F7,    KC.F8,   KC.F9,   KC.F10,  KC.F11,
        XXXXXX, KC.MW_LT, XXXXXX, KC.MS_UP, XXXXXX,   KC.MW_UP, ______,                        ______,   KC.HOME, XXXXXX,  KC.UP,   XXXXXX,   KC.PGUP, KC.F12,
        XXXXXX, KC.MW_RT, KC.MS_LT, KC.MS_DN, KC.MS_RT, KC.MW_DN,                                        KC.END,  KC.LEFT, KC.DOWN, KC.RGHT,  KC.PGDN, XXXXXX,
        ______,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX, KC.MB_MMB, S_RST,       S_RST,    ______,   XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,   XXXXXX,  XXXXXX,
        ______,  ______,  XXXXXX,  XXXXXX,        ______,    KC.MB_LMB, KC.MB_RMB,   ______,   ______,        ______,      KC.HOME, KC.PGUP,  KC.PGDN, KC.END,
    ],
    [   # Numpad
        XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,                          XXXXXX,  KC.NLCK, KC.PSLS, KC.PAST, KC.PMNS,  XXXXXX,   XXXXXX,
        XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  KC.MO(2),                        ______,   XXXXXX, KC.KP_7, KC.KP_8, KC.KP_9,  KC.PPLS,  XXXXXX,
        XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  ______,                          ______,   XXXXXX, KC.KP_4, KC.KP_5, KC.KP_6,  KC.PPLS,  XXXXXX,
        XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,                                             XXXXXX, KC.KP_1, KC.KP_2, KC.KP_3,  KC.PEQL,  XXXXXX,
        ______,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  XXXXXX,  ______,  S_RST,        S_RST,    ______,   XXXXXX, KC.KP_0, KC.KP_0, KC.PDOT,  KC.PEQL,  XXXXXX,
        ______,  ______,  XXXXXX,  XXXXXX,         ______,    ______,  ______,       ______,   ______,        ______,      XXXXXX,  XXXXXX,   XXXXXX,  XXXXXX,
    ],
    [   # Gaming B}
        XXXXXX,  XXXXXX,  ______,  ______,  ______,  ______,  XXXXXX,                          XXXXXX,   ______, ______,  ______,  ______,   XXXXXX,   XXXXXX,
        ______,  ______,  ______,  ______,  ______,  ______,  KC.TO(0),                        ______,   ______, ______,  ______,  ______,   ______,   ______,
        ______,  ______,  ______,  ______,  ______,  ______,  MANAGE,                          ______,   ______, ______,  ______,  ______,   ______,   ______,
        ______,  ______,  ______,  ______,  ______,  ______,                                             ______, ______,  ______,  ______,   ______,   ______,
        ______,  ______,  ______,  ______,  ______,  ______,  ______,  ______,       ______,   ______,   ______, ______,  ______,  ______,   ______,   ______,
        ______,  XXXXXX,  KC.T,    KC.G,         ______,      ______,  ______,       ______,   ______,        ______,     ______,  ______,   ______,   ______,
    ],
    ]

### Main Function ###
if __name__ == '__main__':
    keyboard.go()
