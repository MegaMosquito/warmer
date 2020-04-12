# Warmer -- Software For The Ultimate Cup Warmer!

![Warmer In Use](https://raw.githubusercontent.com/MegaMosquito/warmer/master/images/warmer.jpg)

## Parts

- Mr. Coffee Mug Warmer (https://smile.amazon.com/gp/product/B000CO89T8/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
- RPi ZeroW
- MCP3008
- 2N2222 transistor
- solid state relay
- Thermistor __ ohms
- two buttons
- a "ready" LED
- 5 neopixels (WS2812)
- toggle switch
- power cable and socket
- a few resistors mostly 10K ohms
- wire
- having a 3D printer makes assembly easier, but you could glue stuff in place instead.

## Hardware

The circuitry is shown in the [Fritzing}(http://fritzing.org/home/) document, `circuit.fzz` in this directory.

This is what mine looks like inside:

![Warmer Insides](https://raw.githubusercontent.com/MegaMosquito/warmer/master/images/insides.jpg)

## 3D Models

The 3D models I used for this are here: https://www.tinkercad.com/things/cyHb59UzV8j

## Software

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


