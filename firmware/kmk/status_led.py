from kmk.extensions import Extension
from kmk.scheduler import create_task, cancel_task
from kmk.modules.layers import Layers
from kmk.extensions.lock_status import LockStatus
from kmk.modules.dynamic_sequences import DynamicSequences, SequenceStatus
from kmk.extensions.RGB import RGB

class CustomColors:
    AMBER   = ( 11, 255,  70)
    PRICKLY = (250, 255,  70)
    DEEP    = (180, 255,  70)
    WHITE   = (  0,   0,  70)
    BLIND   = (  0,   0, 200)
    OFF     = (  0,   0,   0)


    # Old RGB stuff - remove?
    #AMBER = (241, 136, 5, 0)
    #PRICKLY = (240, 2, 109, 0)
    #DEEP = (47, 65, 130, 0)
    #BLIND = (200, 200, 200, 200)jkl
    #OFF = (0, 0, 0, 0)

class RGBLite():
    pass


class LEDStatus(Extension):
    def __init__(self,
                keyboard = None,
                rgb: RGB = None,
                layers: Layers = None,
                layer_leds: list[int] = [],
                layer_colors: list[tuple] = [],
                locks: LockStatus = None,
                caps_lock_leds: list[int] = [],
                num_lock_leds: list[int] = [],
                dynamic_sequences: DynamicSequences = None,
                macro_leds: list[int] = [],
                ind_color_1: CustomColors = CustomColors.WHITE,
                ind_color_2: CustomColors = CustomColors.AMBER,
                ind_color_3: CustomColors = CustomColors.DEEP,
                ):
        self.keyboard = keyboard
        self.rgb = rgb

        self.layers = layers
        self.layer_leds = layer_leds
        self.layer_colors = layer_colors
        self._last_layer = 0

        self.locks = locks
        self.caps_lock_leds = caps_lock_leds
        self.num_lock_leds = num_lock_leds

        self.dynamic_sequences = dynamic_sequences
        self.macro_leds = macro_leds
        self._bound = []
        self._flashing = []
        self._flash_on = False
        self._flash_task = None

        self.ind_color_1 = ind_color_1
        self.ind_color_2 = ind_color_2
        self.ind_color_3 = ind_color_3

    def _update_layers(self):
        update = False
        # Check if layer changed, if so update
        if self._last_layer != self.keyboard.active_layers[0]:
            self._last_layer = self.keyboard.active_layers[0]
            update = True
            color = self.layer_colors[self._last_layer]
            for index in self.layer_leds:
                self.rgb.set_hsv(color[0], color[1], color[2], index)

        self.need_update = update

    def _update_locks(self):
        # Caps lock color logic
        if self.locks.get_caps_lock():
            update = True
            for index in self.caps_lock_leds:
                color = self.ind_color_1
                self.rgb.set_hsv(color[0], color[1], color[2], index)
        else:
            update = True
            for index in self.caps_lock_leds:
                color = CustomColors.OFF
                self.rgb.set_hsv(color[0], color[1], color[2], index)

        # Num lock color logic (Only applies to layer 2)

        if self.keyboard.active_layers[0] == 2:
            if self.locks.get_num_lock():
                update = True
                for index in self.num_lock_leds:
                    color = self.ind_color_1
                    self.rgb.set_hsv(color[0], color[1], color[2], index)
            else:
                update = True
                for index in self.num_lock_leds:
                    color = CustomColors.OFF
                    self.rgb.set_hsv(color[0], color[1], color[2], index)

        self.need_update = update

    def _update_macros(self):
        update = False
        status = self.dynamic_sequences.status
        current_ind = self.dynamic_sequences.current_ind

        # Only update if on layer 0
        if self.keyboard.active_layers[0] == 0:
            # Set bound macros to second color
            for x in range(4):
                if len(self.dynamic_sequences.sequences[x+1].sequence_data) > 3:
                    color = self.ind_color_2
                    self.rgb.set_hsv(color[0], color[1], color[2], self.macro_leds[x])
                    if x not in self._bound:
                        self._bound.append(x)
                        self.need_update = True


            # Flash while recording
            if status == SequenceStatus.RECORDING:
                color = self.ind_color_1
                self.rgb.set_hsv(color[0], color[1], color[2], self.macro_leds[current_ind-1])
                self.need_update = True

    # Main update function
    def update_colors(self,):
        self.need_update = False
        #print("updating locks")

        # Update layer colors
        self._update_layers()

        # Update lock colors
        self._update_locks()

        # Update macro colors
        if self.macro_leds:
            self._update_macros()
        if self.need_update:
            self.rgb.show()

    def on_runtime_enable(self, sandbox):
        return

    def on_runtime_disable(self, sandbox):
        return

    # Create scheduled task for updating colors
    def during_bootup(self, sandbox):
        self._task = create_task(self.update_colors, period_ms=(100))

    def before_matrix_scan(self, sandbox):
        return

    def after_matrix_scan(self, sandbox):
        return

    def before_hid_send(self, sandbox):
        return

    def after_hid_send(self, sandbox):
        return

    def on_powersave_enable(self, sandbox):
        return

    def on_powersave_disable(self, sandbox):
        self._do_update()

    def deinit(self, sandbox):
        return
