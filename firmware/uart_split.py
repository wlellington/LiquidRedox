from kmk.modules.split import Split as _Split
from kmk.modules.split import SplitType, SplitSide


# Overwitten Split class that allows multiple other modules to share
#   the UART connection. This requires overloading the receive_uart function pretty
#   heavily as well as adding and managing some additional message queues on both
#   sides of the connection.
#   In essence, this lets the user write new versions of existing modules that add UART
#   messaging to allow split keyboards to behave as expected
class Split(_Split):
    def __init__(self,
                *args,
                **kwargs):
        super().__init__(*args, **kwargs)


        self.uart_modules = {}
        self.uart_modules["KEYBOARD_SPLIT"] = self.uart_header
        self.module_queues = {}
        self.module_queues["KEYBOARD_SPLIT"] = []
        self.serializers = {}
        self.serializers["KEYBOARD_SPLIT"] = self._serialize_update
        self.deserializers = {}
        self.deserializers["KEYBOARD_SPLIT"] = self._deserialize_update

    def get_target(self):
        return self._is_target

    # Enrolls a new submodule and/or extensions to share the UART connection.
    #   This requires a  module name key, **UNIQUE** header byte,
    #   serializer (for sending), and a deserializer (for receiving)
    def add_uart_share(
                        self,
                        module_name = None,
                        header = None,
                        serialize = None,
                        deserialize = None,
                        ):
        print("Enrolling UART module: ", module_name)
        self.uart_modules[module_name] = header
        self.module_queues[module_name] = []
        self.serializers[module_name] = serialize
        self.deserializers[module_name] = deserialize

    # Default keyboard spit uart overload to allow existing Split() functionality
    #   to work out of the box
    def _send_uart(self, update):
        self.send_uart(update, "KEYBOARD_SPLIT")

    # Expanded uart transmission function that uses custom header to allow reciever to
    #   decode messages from each module and assign to appropriate queue
    def send_uart(self, update, module_name):
        if self._uart is not None:
            # Encode to bytes based on user provided serializer
            data = self.serializers[module_name](update)
            # Header (per module)
            self._uart.write(self.uart_modules[module_name])
            # Two byte payload
            self._uart.write(data)
            # Checksum
            self._uart.write(self._checksum(data))
            if module_name != "KEYBOARD_SPLIT":
                print("Writing module {} data to uart: {}".format(module_name, data))

    # Default keyboard spit uart overload to allow existing Split() functionality
    #   to work out of the box
    def _receive_uart(self, keyboard):
        self.receive_uart(keyboard)

    # Overwitten/new receive function to decode incoming messages and store data updates to
    #   module/extension specific queue for processing in each modules update loops.
    def receive_uart(self, keyboard):
        # check that _uart is set up - you really shouldnt be here if youre using ble
        if self._uart is not None and self._uart.in_waiting > 0 or self._uart_buffer:

            # Ensure uart connection is functioning, if not reset
            if self._uart.in_waiting >= 60:
                # This is a dirty hack to prevent crashes in unrealistic cases
                import microcontroller
                microcontroller.reset()

            # Consume UART bytes
            found_module_name = None
            while self._uart.in_waiting >= 4:

                # Grab byte assiming its a header, figure out what module it belongs to
                header = self._uart.read(1)
                found_module_name = None
                for module_name, header_val in self.uart_modules.items():
                    if header == header_val:
                        found_module_name = module_name
                        print("Received header {} [{}]".format(header_val, found_module_name))

                # If a valide module header is found, read message and decode
                if found_module_name:
                    data = self._uart.read(2)
                    # check the checksum
                    if self._checksum(data) == self._uart.read(1):
                        # Find and apply  submodule deserializer
                        update = self.deserializers[found_module_name](data)
                        # If its the base keyboard split module, behave as it would have by default
                        if found_module_name == "KEYBOARD_SPLIT":
                            self._uart_buffer.append(update)
                        # Otherwise, put it in the processing queue for the other modules
                        else:
                            print("Receiving module {} data from uart: {}".format(found_module_name, update))
                            self.module_queues[found_module_name].append(update)

            # Remove items from uart buffer so that updates dont hang around for ever.
            #   Issues with this can cause the keyboard to keep issuing the same keypress/action
            #   over and over (and possibly hanging the host machine)
            if found_module_name == "KEYBOARD_SPLIT" or found_module_name is None:
                if self._uart_buffer:
                    keyboard.secondary_matrix_update = self._uart_buffer.pop(0)
