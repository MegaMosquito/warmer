FROM arm32v6/python:3-alpine
WORKDIR /usr/src/app

# Install build tools
RUN apk --no-cache --update add gawk bc socat git gcc libc-dev linux-headers scons swig

# Clone, build and install the python NeoPixel library
RUN git clone https://github.com/jgarff/rpi_ws281x.git
RUN cd /usr/src/app/rpi_ws281x; mv SConscript SConscript.orig; sed 's/0755/0o755/' SConscript.orig > SConscript
RUN cd /usr/src/app/rpi_ws281x; scons
RUN cd /usr/src/app/rpi_ws281x/python; python setup.py install

# Install the python GPIO library
RUN pip install RPi.GPIO

# Install the python library (for the MCP3008, 8-channel 10-bit A-to-D chip)
RUN pip install adafruit-mcp3008

# Install flask (for the web server)
RUN pip install Flask

# Copy over the required files
COPY ./html/ ./html/
COPY ./images/ ./images/
COPY ./favicon.ico .
COPY ./warmer.py .

# Run the daemon
CMD python warmer.py

