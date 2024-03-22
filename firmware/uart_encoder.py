from kmk.modules.split import Split, SplitType, SplitSide
from kmk.modules.encoder import EncoderHandler as _EncoderHandler
from kmk.modules.encoder import GPIOEncoder as _GPIOEncoder
from micropython import const
from supervisor import runtime
import usb_hid
import digitalio
import busio
import traceback

# Overloaded GPIOEncoder capable of having null pins
class GPIOEncoder(_GPIOEncoder):
    def __init__(self,
                pin_a=None,
                pin_b=None,
                pin_button=None,
                is_inverted=False,
                divisor=None,
                button_pull=digitalio.Pull.UP,
                ):

        # Create dummied out encoder if pins are None
        if pin_a is None and pin_b is None:
            print("Creating dummy encoder...")
            self.pin_a = None
            self.pin_b = None
            self.pin_button = None
            self._state = (
                            # Pin a
                            {
                            'direction': None,
                            'position': None,
                            'is_pressed': None,
                            'velocity': None,
                            } ,

                            # Pin B
                            {
                            'direction': None,
                            'position': None,
                            'is_pressed': None,
                            'velocity': None,
                            }
            )
            self._start_state = self._state
            self.divisor = divisor

        # Create normal encoder
        else:
            super().__init__(
                            pin_a=pin_a,
                            pin_b=pin_b,
                            pin_button=pin_button,
                            is_inverted=is_inverted,
                            divisor=divisor,
                            button_pull=button_pull,
                            )


    # Overloaded update function to be capable of skipping pin updates
    def update_state(self):
        # Skip over updates on nulled out pins
        if self.pin_a is None and self.pin_b is None:
            return

        return super().update_state()

# Container to hold upate (just a syntax nicety)
class EncoderUpdate():
    def __init__(
                self,
                encoder: int = 0,
                active_layer: int = 0,
                index: int = 0,
                ):
        # First half of first byte
        self.encoder = encoder

        # Second half of first byte
        self.active_layer = active_layer

        # Second byte
        self.index = index

# Overwritten class to support UART comms
# DATA FLOW:
#   HOST (USB connected) <-- CLIENT (non-usb)
#   Applies Encoder Map      Sends Encoder Activity
class EncoderHandler(_EncoderHandler):
    def __init__(self,
                split: Split = None,
                host_side: bool = True,
                *args,
                **kwargs):
        super().__init__(*args, **kwargs)

        # Additional uart boiler plate to work with modified uart_split
        assert isinstance(split, Split), "No split provided for EncoderHandler!"
        self._split = split
        self._uart = self._split.get_uart()
        self.uart_header = bytearray([0xD7])
        self.module_name = "ENCODER_HANDLER"
        self.host_side = None

        # Enroll uart handling with the split module
        self._split.add_uart_share(
                        module_name = self.module_name,
                        header = self.uart_header,
                        serialize = self._serialize_update,
                        deserialize = self._deserialize_update,
                        )


    # Overloaded to add ability to create dummied encoder and report creation to console
    def during_bootup(self, keyboard):
        # Determine which side is the host based on presence of USB connection
        if runtime.usb_connected:
            self.host_side = True
        else:
            self.host_side = False

        assert self.host_side is not None, "Host side not set!"

        #Normal boot up behavior
        if self.pins and self.map:
            for idx, pins in enumerate(self.pins):
                print("Attempting to create encoder with pins: ", pins)
                try:
                    # Check for none, dummy encoder if some
                    if pins is None:
                        new_encoder = GPIOEncoder()
                        self.encoders.append(new_encoder)

                    else:
                        # Check for busio.I2C
                        if isinstance(pins[0], busio.I2C):
                            new_encoder = I2CEncoder(*pins)

                        # Else fall back to GPIO
                        else:
                            new_encoder = GPIOEncoder(*pins)
                            # Set default divisor if unset
                            if new_encoder.divisor is None:
                                new_encoder.divisor = self.divisor

                        # In our case, we need to define keybord and encoder_id for callbacks
                        new_encoder.on_move_do = lambda x, bound_idx=idx: self.on_move_do(
                            keyboard, bound_idx, x
                        )
                        new_encoder.on_button_do = (
                            lambda x, bound_idx=idx: self.on_button_do(
                                keyboard, bound_idx, x
                            )
                        )
                        self.encoders.append(new_encoder)
                        print("Added encoder on: {}".format(pins))
                except Exception as e:
                    print("Create encoder error: {}".format(e))
                    print("Encoder Error pins: {}".format(pins))
                    print(traceback.format_exception(e))
        print(self.encoders)
        return

    # Overload of encoder movement function. Host immediately activates key,
    #   client sends UART message to host
    def on_move_do(self, keyboard, encoder_id, state):
        if self.map:
            layer_id = keyboard.active_layers[0]
            # if Left, key index 0 else key index 1
            key_index = 0
            if state['direction'] == -1:
                key_index = 0
            else:
                key_index = 1

            # If host, issue to keyboard
            if self.host_side:
                key = self.map[layer_id][encoder_id][key_index]
                keyboard.tap_key(key)
                print("Tapped: {}".format(key))
            # If not host, write to uart
            else:
                update = EncoderUpdate(
                                        encoder=encoder_id,
                                        active_layer=layer_id,
                                        index=key_index,
                                        )
                self._split.send_uart(update, self.module_name)

    # Overload of encoder button press function. Host immediately activates key,
    #   client sends UART message to host
    def on_button_do(self, keyboard, encoder_id, state):
        if state['is_pressed'] is True:
            layer_id = keyboard.active_layers[0]

            # If host, issue to keyboard
            if self.host_side:
                key = self.map[layer_id][encoder_id][2]
                keyboard.tap_key(key)
                print("Host Tapped: {}".format(key))
            # If not host, write to uart
            else:
                update = EncoderUpdate(
                                        encoder=encoder_id,
                                        active_layer=layer_id,
                                        index=2,
                                        )
                self._split.send_uart(update, self.module_name)

    # Encode object into bytes
    def _serialize_update(self, update):
        buffer = bytearray(2)
        compound = (update.active_layer << 4) | update.encoder
        buffer[0] = compound
        buffer[1] = update.index
        return buffer

    # Decode bytes into object
    def _deserialize_update(self, raw_update):
        update = EncoderUpdate(
                                encoder=raw_update[0] & 0x0F,
                                active_layer=(raw_update[0] & 0xF0) >> 4,
                                index=raw_update[1],
                                )
        return update

    # Read data from uart to check for updates
    def after_matrix_scan(self, keyboard):
        super().after_matrix_scan(keyboard)
        # Host grabs data from client side, writes to actions
        if self.host_side:
            if len(self._split.module_queues[self.module_name]) > 0:
                update = self._split.module_queues[self.module_name].pop(0)
                # Issue new key
                key = self.map[update.active_layer][update.encoder][update.index]
                keyboard.tap_key(key)
                print("UART Tapped: {}".format(key))
