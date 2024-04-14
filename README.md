# LiquidRedox
A completely custom, 3D printed, split mechanical keyboard based on the Adafruit KB2040, programmed with the [KMK Firmware](http://kmkfw.io/)

![LiquidRedox Keyboard](https://github.com/wlellington/LiquidRedox/blob/main/images/top_view.jpg)
![LiquidRedox Keyboard](https://github.com/wlellington/LiquidRedox/blob/main/images/angled_view.jpg)

## About

This keyboard was born out of the desire to have a fully featured split keyboard that did not rely too heavily on sophisticated layer tricks. It started with the [Redox Media](https://github.com/shiftux/redox-media-keyboard) remix of the original [Redox Keyboard](https://github.com/mattdibi/redox-keyboard), but was tweaked to make some more complex features directly accessable. With that goal in mind, I added four additional keys per side for special functions and as well as a pair of clickable rotary encoders. This created two somewhat large keyboard halves, but gave me enough room for the extra features and increased usability that I wasnted. I decided to keep the outermost column to normal 1U keycaps (rather than the Redox's 1.25s), mostly so keycap sets with legends are easy to find.

It is built around two Adafruit KB2040s, using a two pin UART connection via a TRRS cable. The internals are all hand-wired in a standard diode matrix made up of 6 rows and 7 columns, though there are some empty spots created by the top row for the extra keys. The encoders are standard GPIO style encoders that require 3 pins each (clock, data, and button). There are a few neopixel LEDs tucked under the extra keys and the shift key to act as basic status indicators, but the rest of the board is not backlit.

To facilitate on-the-fly reprogramability and the ability to see and update the keymap without need for a full toolchain, I went with KMK for the firmware, but that could be easily changed to QMK on a similar (or the same) microcontroller if desired. 

## Features
There are a few unique features that I had not seen on other KMK based builds that were made possible with the custom firmware and module modifications I wrote for this project. I added some additional functionality to a few of the base modules/extensions to allow for use over a UART connection so that only a few parts of existing library components need to be tweaked to allow for full Split compatability.

1. Fully split configurations with identical firmware on each half (to make source management easy)
2. Two rotary encoders (one per side) that both function even when one only one side is connected to the host computer
3. Status RGB lights that are tied to things like layer, host side lock information, and dynamic macro binding
4. **A modified KMK Split module that allows multiple modules/extensions to share the UART connection for message passing**
5. Dynamic Macros that can be recorded and bound to a specific macro key for easy of use

## Usage Notes

#### Layers
There are three layers in the firmware in this repo:
1. The QWERTY Layer - there are some funky placements for a few symbol keys, but it generally follows the traditional keyboard layout
2. The Navigation Layer - this adds arrow keys on the IJKL set and mouse keys centered on the ESDF keys. There are also function keys on the number row
3. The Numpad Layer - this converts the right side into a numpad, complete with status indicated numlock key

#### Dynamic Macros
This firmware allows the user to record an on-the-fly macro to one of four slots (the top four keys on the right hand side). The recording process is as follows:
1. Tap the "Record Key" (the top 1U Key on the right hand sides inner extra cluster by 6 and Y)
2. Tap the macro key on the top row that you want to save your macro to (top row of right side by encoder). A light will indicate that the slot is selected after tapping
3. Type whatever action/macro/key combination you want
4. Tap either the target macro key, the record start key, or any other macro key to stop recording. The slot will change to a secondary color indicating that it is full, but not being recorded to
5. Tap the macro key that you wish to play whenever you want
NOTE: These macros do not persist across power cycles and will not be able to capute actions created by the rotary encoders.

#### Connecting Storage
By default, the keyboard will not present its USB-drive storage device when plugged in, so as to keep windows from recognizing the drive each time you plug in the keyboard. To enable storage, hold the top, inner-most key on each keyboard's thumb cluster during power on when first plugged in. See the boot.py file for these settings.

## Software Implementation Notes

This whole project is running off of standard KMK modules, so you will need to follow the standard instructions for installing [CircuitPython](https://learn.adafruit.com/welcome-to-circuitpython/installing-circuitpython) and [KMK](http://kmkfw.io/docs/Getting_Started/). I made a few changes within the KMK library during my experiements, but most if not all should have been reveresed and the necessary changes moved to the overload classes provided in the top level of the firmware directory. If you do find an issue related to a non standard KMK module edit that I left in by mistake, please let me know.

I recommend you ensure that the firmware and the UART connection are working before you start soldering things together, just to make sure everything works. In fact, in my own testing, I temporarily soldered the UART and power pins of both controller boards together to verify that I could get the UART connection at least partially working before moving on to later steps of the project.

#### UART Support
One of the major downsides of the KMK Split module as it currently exists, is that it does not allow for any other modules to use it's UART connection to communicate. This means that any other modules you install that are not directly tied to the keymap (like encoders, lock key status, etc.) will not work when you first set things up. This is because the Split module is essentially only passing over the index of the key being pressed from the client side (side not connected to the computer) to the host side (side connected to the computer). This means that other modules will not be able to share their information, which manifests as the modules on the client side (mostly) not working. I first noticed this when testing the encoder module, as it does not directly interact with the keyboard matrix scanners or updates, to the Split Module can do nothing to share encoder updates from keyboard half to keyboard half. This means that the encoder on the side plugged into the computer will work fine, but the other side will not. After a fair amount of reading forum threads and PRs on the KMK github, I realized that there probably was not a simple/established solution to this, so I implemented my own.

To fix this, I have written several expansion classes (overloaded classes?) that re-implement a few features to make it possible for the Split module to oversee communications between not only the keyboard matrix, but any other modules you choose to employ. In this repo, I added UART support for the Encoder module and LockStatus module so that the keyboard halves always perform as expected no matter which side is plugged in. The most important changes can be seen in [uart_split.py](https://github.com/wlellington/LiquidRedox/blob/main/firmware/uart_split.py) which completely overhauls the UART receiving handler so that rather than expecting only one UART headerv (defined by the split module itself), it can use a list of headers (enrolled during setup) to determine which modules are trying to communicate, how to decode their communications, and which "message queue" to store their output in. With this modification to Split, the user can tweak other extensions/modules to send formatted UART messages from either side (assuming a two wire UART connection), as well as receive messages from the other half.

For example: The Encoder module generates messages on the client side (not connected to computer) and sends them to the host side. On the host side, the messages are decoded and interpreted as the corresponding keyboard taps. Since the encoder keymap is set for both sides, I also added the ability to add a None'd out encoder to serve as a placeholder on each side. This way the keymap between sides looks the same, but you can create a fake encoder that does not get updated, all while keeping the EncoderHandler happy. The implementation of this can be seen in [uart_encoder.py](https://github.com/wlellington/LiquidRedox/blob/main/firmware/uart_encoder.py)
For example: The LockStatus module generates capslock and numlock status messages depending on what the computer's USB interface reports. The host side then formats and sends these messages to the client side, where they are decoded and used to update the clients understanding of the computers lock state. This is important mostly because capslock and numlock are on opposite halves of the keyboard, yet only the side connected to the computer actually knows what the host computer's key lock status is. In this firmware, this is used to control indicator lights. [uart_lock_status.py](https://github.com/wlellington/LiquidRedox/blob/main/firmware/uart_lock_status.py)

Check out the uart_*.py files to understand how this is done in each module. Keep in mind that you need to **import the overloaded version in your code.py in order for the changes to have effect**.

#### Goofy Pin Maps
The split module usually assumes that the two halves of the keyboard are identical, and just have the column wires swapped. I dont like this because it assumes two things - 1) each half has the same keys/layout, 2) that the same keys/layout are implemented in the same way. To get around this, I wrote a custom [kb.py](https://github.com/wlellington/LiquidRedox/blob/main/firmware/kb.py) that automatically detects which side it is booting on and assigns the pin map accordingly. This means you can mess up wiring your pins (like I did) and fix it in the software or even have asymetrical keyboards! 

One thing to keep in mind is that the scanning order is set by the coord_mapping list in the keyboard class. This is the order that the scanner will traverse the keys according to what it thinks is row and column zero, up through the pin list provided. When split, it tries to cut this mapping in half, where all the keys on the second keyboard (the right side) will be scanned "after" the left hand board. In reality, this Split module will just cut the list in half and just iterate over the second half of the map by calculating an offset to jump to the right scanning location. While I have not yet attempted an asymetrical board, I suspect that you might need to make separate coord_mappings for each half if you wanted the shape/number of keys to be different.

#### Status RGB LED Lighting
I have never been one for RGB lighting animations, but I do like having status indication lights or monocrome back lighting. For this keyboard, I added five neopixels per side so that I could get a sense of what layer I was on, which locks were enabled, etc.. For this, I implemented the LEDStatus class in [led_status.py](https://github.com/wlellington/LiquidRedox/blob/main/firmware/status_led.py). This should not be confused with the built in Status LED extension in KMK, as it shares no code with it. It takes in information from the attached LockStatus, DyanimicSequences, and Layers modules and runs a scheduled task to update specific LED colors whenver changes occur. It currenlty expects all of these modules to be in use, so if you choose to remove something like the DynamicSequences, you may need to edit the LEDStatus class further to remove the dependence.

This custom extension uses an overloaded RGB class object from the KMK RGB extension to manage the LEDs themselves. My custom implementation just adds a function to let the user statically set an LED's color based on a HSV value where None can be used to keep existing settings (like brightness). It does not change the way that the animations work or are rendered, but gives finer grain control over the color of the LEDs you might want to specifically color for indicators. It wasnt really intended to be used in concert with other animations, but just to color things for this specific layout.

![Backlighting](https://github.com/wlellington/LiquidRedox/blob/main/images/backlighting.jpg)

## Build Notes

#### The Case
The case was orgininally based on the [Redox Media](https://github.com/shiftux/redox-media-keyboard) project, which has a very nice instructional/educational video to accompany it. However, I decided that I wanted to make something a bit more "flat" in terms if the case design (more like this project [Redox Neo](https://github.com/Pastitas/Redox-neo-Case)), so I took the base cad files from Redox Media and created a new design that keeps the encoder flush with the rest of the keys and adds 4 more slots for mechanical keys at the top of the board. This lead to a similar two peice design (top half plate, bottom half case) that was fairly easy to print and iterate on. In the end, the only shared part of the design was the base keylout itself, as I had to redesign just about every other component of the case. I went with countersunk M3 screws to hold things together.

![Layout Render](https://github.com/wlellington/LiquidRedox/blob/main/images/fusion_layout.JPG)

The bottom case was designed to only be as thick as it needed ot be, since I wanted something that was not overly bulky. Balancing this was somewhat difficult, and to took a few iterations to get enough room for the encoder boards, USB-C panel mount adapter (which I had to modify anyway), and the TRRS jack (more on those later).

![3D Case Render](https://github.com/wlellington/LiquidRedox/blob/main/images/fusion_screenshot.JPG)

The main issue with the case came down to the tolerancing of the holes for the switches. At first, I made the holes a bit too small (using the same tolerancing from the Redox Media layout). The switches were snug and held in well, but I soon realized that cramming the switches into these slightly too tight spaces caused the panel to curl upward around the edges (like a potato chip), creating gaps around the edges where the two halves of the case would meet. 

![Flex Issue](https://github.com/wlellington/LiquidRedox/blob/main/images/gap_issue.jpg)

I solved this by adding a bit more tolerance to the switch mount holes and reprinting. This seemed to work at the time, but by the time I painted everything I had added back enough material to reintroduce the problem. This part of the design is somethign that could certainly be improved on in the future. I also added an extra standoff peg/pylon in the center of the board (looks like a screw mount colum with no hole in it) to support the keybed in the middle to give it a firmer feel and reduce flex.

I printed the parts with fairly low infill (since they were so thin) and relatively high wall thickness (4 layers) on my Creality CR-10. Each plate took about 6.5 hours to print, and each bottom case took about 9 hours, but that will vary a lot depending on your print settings. I just used some plain black PLA for this, as I didnt want any light transmission even though I wanted a white case.

After printing, I sanded down the layer lines and rough features with 120 grit sandpaper. This process took ages, but ended up being worth it in the end. Once sanded and cleaned, I gave the case peices several layers of high build primer ([like this](https://www.rustoleum.com/product-catalog/consumer-brands/auto/primers/2-in-1-filler-and-sandable-primer)) and touched up spots over the course of several hours where more filling was necessary. Once dry (a day or so), I wet sanded the case parts down with fine grit sandpaper (800 grit) to smooth out the surface layer of the primer. I let it dry for another two days or so and then did many light coats of a standard white rustoleum flat spray paint. In my testing, I also tried a layer of clearcoat, but this gave it a plasticy sheen I did not like, so I elected to leave the final layer just the flat white paint. I let this dry for a few days before working with it again, since the paint seemed somewhat soft 24 hours later.

After everything was dry, I started installing the switches (I used [TTC Venus'](https://mechanicalkeyboards.com/products/ttc-venus-45g-linear-pcb-mount-switch?_pos=1&_sid=83bf7ec0e&_ss=r) since they are buttery smooth and have a nice "thock"). I noticed that my edge gaps had come back (presumably since the paint had added to the tolerances on the switch holes), so I *very gently heated the spreading spots with a hair dryer while clamping the gaps shut with the screws and switches all installed*. This is a very, very delicate process as too much heat too fast can cause PLA to warp in weird ways, so I took my time with this and kept the hair dryer moving constantly and only applied heat around the areas that needed to be relaxed. I also recommend putting a peice of paper between the part and the clamps to keep the clamps from maring or discoloring the surface of the white paint.

![Flex Issue After Paint](https://github.com/wlellington/LiquidRedox/blob/main/images/gap_issue_after_paint.jpg)

#### The Electronics
Once happy with the fit, I moved on to the wiring. I dont have to many notes on this whole process, since it was pretty straight forward overall. I think there are a lot of handwired keyboard projects out there that explain the matrix wiring pretty well, so I'll lean on them to better explain things. Check out some of the other linked projects in this README to get better examples.

Heres a link to the pinout for the board I used: [KB2040 Pinout](https://learn.adafruit.com/adafruit-kb2040/pinouts)

That said, I should note that I used a few pins on the KB2040 that the docs do not explicitly state you can use for matrix scanning. Since all of the pins on RP2040 microcontroller itself are GPIO, they can serve many purposes beyond just what the circuit board silkscreen mentions. To that end, I used almost every pin on the board including MISO, MOSI, SCK, etc. for matrix scanning functions. In addition, I bought a pack of [Qwiic](https://www.sparkfun.com/qwiic) (or "4 Pin JST", or "STEMMA QT" as Adafruit and others might call it) connector cables and cut them up so that I could access the SDA and SCL pins hidden inside the connected jack. This gave me more pins to play with and is how I had enough room to add the Neopixel lighting signal. The encoders each took three pins as well as a connection to power and ground. 

Ideally, both sides would be wired the exact same way. I made a few mistakes in keeping my pin map consitent, but luckily I found a way to fix this in the firmware and it was not an issue in the end (See "Goofy Pin Maps").

![Wiring](https://github.com/wlellington/LiquidRedox/blob/main/images/wiring.jpg)

I bought a panel mount USB-C connector (which the case design takes into account) rather than try to make the microcontroller mount cleanly to the outside of the case. [Here](https://www.amazon.com/dp/B086YBP5VW?ref=ppx_yo2ov_dt_b_product_details&th=1) is the one I used, but if you end up needing a different cable, you will likely need to tweak the case design to accomidate different screw holes or a snap in type connector. I used [some standard TRRS](https://www.amazon.com/dp/B06XG3YTC4?psc=1&ref=ppx_yo2ov_dt_b_product_details) jacks (with some heatshrink) to make the UART connections. I attached the RAW pin of the KB2040 to the sleeve of the cable, UART to the two rings, and power to the tip. I had to whittle away some of the plastic on the USB-C connector's panel side to make it fit the curve of the case, and completely removed the outer most layer of plastic on the side that connects to the KB2040 to save some room on thickness.

**TRRS style connectors can be a bit dangerous since there is a potential to short power to ground when inserting/removing the cable. I recomment only plugging/unplugging the connection cable when the keyboard is completely unplugged from the Computer.** I specifically chose to put the ground on the tip (since it is most likely to touch other contacts on insertion, and power on the sleeve, since it is the last to make contact.

![Jacks](https://github.com/wlellington/LiquidRedox/blob/main/images/jacks.jpg)

I recommend not screwing everything together till you know your firmware is working however, since you are likely causing a bit a damage to the screw holes each time you insert/remove the case screws. This means that theres a finite number of times you can add or remove the screws. In my process, I have problably done this six or seven times, but I am hesitant to open and close the case all willy-nilly. Since software troubleshooting can be a bit tricky (I had issues where the serial connection would drop out on me), I recommend leaving the case open so you can reach your microcontroller's reset button until you are close to finished.

When everything was said and done, I put some little black rubber dome feet on the bottom to keep the paint from scratching off on my desk surface and make the whole thing a bit more stable. I also packed a few small peices of foam between the LEDs and their surrounding components to help reduce light bleed.


### Tenting Wedges
To help make the angle of things feel a bit more natural, I have also designed a tenting wedge that can be printed and placed under each half. The wedges add a 5 degree angle up from front to back of the keyboard, and five degrees up from outside to inside. This does add some considerable hight to the whole thing, but so far I have found them to be pretty comfortable. The wedges are perfectly symmetrical, so just flip the provided half in your slicer when you need both.

The wedges were designed with the rubber feet in mind, so use the wedges as a template to place your feet if you decide to add the tenting. The holes are all just 10 mm in diameter, so common rubber feet of around that size should work well. I added places on the bottoms of the wedges for feet as weel, but the addition height might not be worth it.

## TODO + Future Work
1. ~~Add "On Sleep" functions to turn off LEDs when host machine goes to sleep~~ (Done)
2. Add wake function to wake host machine?
3. Add ability to loop dynamic macros - RapidFire currently causes a pystack exhaustion
4. Add unicode send strings to send emoticons - this currently causes a pystack exhastion using the unicode_sequence module
5. ~~Add tenting wedge for mor ergonomic angle~~ (Done)
