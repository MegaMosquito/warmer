# Warmer -- Software For The Ultimate Cup Warmer!

![Warmer In Use](https://raw.githubusercontent.com/MegaMosquito/warmer/master/images/warmer.jpg)

## Parts

- Mr. Coffee Mug Warmer (https://smile.amazon.com/gp/product/B000CO89T8/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
- plastic box (I used a Serpac enclosures, 6.88 x 4.88 x .92, but they don't sell that on Amazon any more. I think [this enclosure](https://smile.amazon.com/Serpac-171-Plastic-Enclosure-Length/dp/B00B88CC0Y/ref=sr_1_fkmr2_1?dchild=1&keywords=serpac+Enclosures%2C+Boxes%2C+%26+Cases+6.88+x+4.88+x+.92+Black&qid=1586725240&sr=8-1-fkmr2) would work well though. Or you could 3D print something.
- small 5V power adapter, like an iPhone charger, and 2 amps is more than enough
- RPi ZeroW
- MCP3008
- 2N2222 transistor
- solid state relay
- Thermistor __ ohms
- two buttons
- a "ready" LED
- 5 neopixels (WS2812) to show time remaining and current temperature
- toggle switch for high voltage power on/off
- power cable and socket
- a few resistors mostly 10K ohms
- wire
- liquid electrical tape (optional...  it's the big black blob covering the high voltage connections in the hardware photo)
- having a 3D printer makes assembly easier, but you could glue stuff in place instead.

## Hardware

The circuitry is shown in the [Fritzing}(http://fritzing.org/home/) document, `circuit.fzz` in this directory.

This is what mine looks like inside:

![Warmer Insides](https://raw.githubusercontent.com/MegaMosquito/warmer/master/images/insides.jpg)

## 3D Models

The 3D models I used for this are here: https://www.tinkercad.com/things/cyHb59UzV8j

## Software

The software monitors the buttons, and acts accordingly to increase or decrease the timeout for the cup warmer. It also monitors the thermistor to know the current temperature of the warming plate (I epoxy-ed the thermistor onto the bottom on the metal heating plate near the heating element). The software also displays the current temperature of the heating plate by using color on the NeoPixel LEDs (red is hottest, through organe, yellow, green. to blue, the coldest). It also shows the time remaining on the NeoPixels by making the leftmost "N" of them much brighter than the others (i.e., same color, but brighter) to indicate "N" time units remaining.

The software also presents a "digital twin" web UI that looks like the real object, and whose buttons and LEDs function the same as the physical object. The digital twin also shows the precise temperature, and the precise amount of time remaining. Here is an image of the web UI in operation:

![Warmer Web UI](https://raw.githubusercontent.com/MegaMosquito/warmer/master/images/webui.jpg)

Create a `/home/pi/git` directory, then clone this repository into there. Enter this directory, then build and run the Docker container:

```
cd /home/pi/git/warmer
make build
make run
```

### Autostart

To make this code always autostart on boot up, add these lines to the bottom of `/etc/rc.local`, but just above the last `exit 0` line.  You could use `sudo nano /etc/rc.local` to edit this system file and then add this:

```
# Start up the beverage warmer program
su pi -c 'cd /home/pi/git/warmer; make run; 2>&1 &'
```

Then reboot.  That's it!


