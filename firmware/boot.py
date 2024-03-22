# Borrowed + adapted from
# https://github.com/moritz-john/kmk-config-klor/blob/master/firmware/utilities/hide_device_storage/boot.py

import supervisor
import board
import digitalio
import storage
import usb_cdc
import usb_hid
from kmk.hid_reports import pointer

# If this key is held during boot, don't run the code which hides the storage and disables serial
# To use another key just count its row and column and use those pins
# You can also use any other pins not already used in the matrix and make a button just for accesing your storage

left = True if str(storage.getmount('/').label)[-1] == 'L' else False
print("Booting as left:", left)
print("Hold top innermost thumb key to enable storage")

# Select innermost + top most key on both sides
if left:
    col = digitalio.DigitalInOut(board.MOSI) #Col 6
    row = digitalio.DigitalInOut(board.D6)   #Row 2
else:
    col = digitalio.DigitalInOut(board.A2)   #Col 6
    row = digitalio.DigitalInOut(board.D7)   #Row 2

# TODO: If your diode orientation is ROW2COL, then make row the output and col the input
col.switch_to_output(value=True)
row.switch_to_input(pull=digitalio.Pull.DOWN)

# Set usb devices (Mouse required for mouse keys, consumer for media keys)
devices = []
devices.append(usb_hid.Device.KEYBOARD)
devices.append(usb_hid.Device.MOUSE)
devices.append(usb_hid.Device.CONSUMER_CONTROL)


if not row.value:
    print("Disabling Storage + Serial...")
    storage.disable_usb_drive()
    # Equivalent to usb_cdc.enable(console=False, data=False)
    usb_cdc.disable()
    usb_hid.enable(devices, boot_device=1)
else:
    print("Enabling Storage...")

# Pretty sure this does nothing...
supervisor.set_usb_identification("KMK Keyboard", "LiquidLight")

# Free pins for normal behavior
row.deinit()
col.deinit()
