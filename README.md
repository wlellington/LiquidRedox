# LiquidRedox
A completely custom, split mechanical keyboard based on the Adafruit KB2040 programmed with the [KMK Firmware](http://kmkfw.io/)

![LiquidRedox Keyboard](https://github.com/wlellington/LiquidRedox/blob/main/images/20240321_224324.jpg)

## About

This keyboard was born out of the desire to have a fully featured split keyboard that did not rely too heavily on sophisticated layer tricks. It started with the [Redox Media](https://github.com/shiftux/redox-media-keyboard) remix of the original [Redox Keyboard](https://github.com/mattdibi/redox-keyboard), but was tweaked to make some more complex features directly accessable. With that goal in mind, I added four additional keys per side for special functions and as well as a pair of clickable rotary encoders. This created two somewhat large keyboard halves, but gave me enough room for the extra features and increased usability that I wasnted. I decided to keep the outermost column to normal 1U keycaps (rather than the Redox's 1.25s), mostly so keycap sets with legends are easy to find.

It is built around two Adafruit KB2040s using a two pin UART connection via a TRRS cable. The internals are all hand-wired in a standard diode matrix made up of 6 rows and 7 columns, though there are some empty spots created by the top row for the extra keys. The encoders are standard GPIO style encoders that require 3 pins each. There are some neopixel LEDs tucked under the extra keys and the shift key to act as basic status indicators.

To facilitate on-the-fly reprogramability and the ability to see and update the keymap without need for a full toolchain, I went with KMK for the firmware, but that could be easily changed to QMK on a similar (or the same) microcontroller if desired. 

## Features
There are a few unique features that I had not seen on other KMK based builds that were made possible with the custom firmware and module modifications I wrote for this project. I added some additional functionality to a few of the base modules/extensions to allow for use over a UART connection so that only a few parts of existing library components need to be tweaked to allow for full Split compatability.

1. Fully split configurations with identical firmware on each half (to make source management easy)
2. Two rotary encoders (one per side) that both function even when one only one side is connected to the host computer
3. Status lights that are tied to things like layer, host side lock information, and dynamic macro binding
4. **A modified KMK Split module that allows multiple modules/extensions to share the UART connection for message passing**
5. Dynamic Macros that can be recorded and bound to a specific macro key for easy of use

## Usage Notes

#### Layers
There are three layers in the firmware in this repo:
1. The basic QWERTY Layer - there are some funky placements for a few symbol keys, but it generally follows the traditional keyboard layout.
2. The Navigation Layer - this adds arrow keys on the IJKL set and mouse keys centered on the ESDF keys. There are also function keys on the number row.
3. The Numpad Layer - this converts the right side into a numpad, complete with status indicated numlock key

#### Dynamic Macros
This firmware allows the user to record an on-the-fly macro to one of four slots (the top four keys on the right hand side). The recording process is as follows:
1. Tap the "Record Key" (the top 1U Key on the right hand sides inner extra cluster by 6 and Y)
2. Tap the macro key on the top row that you want to save your macro to (top row of right side by encoder). A light will indicate that the slot is selected after tapping
3. Type whatever action/macro/keycombination you want
4. Tap either the target macro key, the record start key, or any other macro key to stop recording. The slot will change to a secondary color indicating that it is full, but not being recorded to
5. Tap the macro key that you wish to play whenever you want
NOTE: These macros do not persist across power cycles and will not be able to capute actions created by the rotary encoders.

## Implementation notes

#### UART Support
WIP

## Build Notes

The case was orgininally based on a project from 
