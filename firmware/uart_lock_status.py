from kmk.modules.split import Split, SplitType, SplitSide
from kmk.extensions.lock_status import LockStatus as _LockStatus
from micropython import const
from supervisor import runtime
import usb_hid

# Container to hold upate (just a syntax nicety)
class LockUpdate():
    def __init__(self, report=0x00):
        self.report = report

# Overwritten class to support UART comms
# UART DATA FLOW:
#   HOST (USB connected) --> CLIENT (non-usb)
#   Sends Host Comp Locks    Receives locks and writes to local status
class LockStatus(_LockStatus):
    def __init__(self,
                split: Split = None,
                host_side: bool = True,
                *args,
                **kwargs):
        super().__init__()

        # Additional uart boiler plate to work with modified uart_split
        assert isinstance(split, Split), "No split provided for LockStatus!"
        self._split = split
        self._uart = self._split.get_uart()
        self.uart_header = bytearray([0xD5])
        self.module_name = "LOCK_STATUS"
        self.host_side = None

        # Enroll uart handling with the split module
        self._split.add_uart_share(
                        module_name = self.module_name,
                        header = self.uart_header,
                        serialize = self._serialize_update,
                        deserialize = self._deserialize_update,
                        )

    # Set host stide, so as to only check for hid stuff on the side connected
    #   to USB
    def during_bootup(self, sandbox):
        if runtime.usb_connected:
            self.host_side = True
            for device in usb_hid.devices:
                if device.usage == usb_hid.Device.KEYBOARD.usage:
                    self.hid = device
            if self.hid is None:
                raise RuntimeError
        else:
            self.host_side = False

    # Encode as bytes
    def _serialize_update(self, update):
        buffer = bytearray(2)
        buffer[0] = update.report
        buffer[1] = 0
        return buffer

    # Decode bytes into object
    def _deserialize_update(self, raw_update):
        update = LockUpdate(
                            report=raw_update[0]
                            )
        return update

    def before_hid_send(self, sandbox):
        super().before_hid_send(sandbox)

    ### Send uart if lock state changed by checking queues - if so write it back
    def after_hid_send(self, sandbox):
        # Only update self.hid information if this side is the target (connected to USB)
        if self.host_side:
            report = self.hid.get_last_received_report()
            if report is None:
                self._report_updated = False
            else:
                self.report = report[0]
                self._report_updated = True

            if self._report_updated:
                print("Updating LockStatus UART")
                update = LockUpdate(report=self.report)
                self._split.send_uart(update, self.module_name)

         # Client side check for data in queue, if its there pop and process
        else:
            if len(self._split.module_queues[self.module_name]) > 0:
                new_update = self._split.module_queues[self.module_name].pop(0)
                print("New data detected for module {}: {}".format(self.module_name, new_update))
                # Overwrite LockStatus report object with received data
                self._report_updated = True
                self.report = new_update.report

