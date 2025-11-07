# AsTeRICS-Grid-Helper: HTTP-to-Serial Bridge
This helper application for [AsTeRICS Grid](https://github.com/asterics/AsTeRICS-Grid) provides a local webserver which forwards AT commands to a connected [FABI](https://github.com/asterics/FABI) or [FlipMouse](https://github.com/asterics/FLipMouse) device. 
It automatically connects to the first compatible device found via scanning the available COM/Serial ports.
This allows using features of FlipMouse or FABI from within AsTeRICS grid (via the HTTP action), for example recording or replaying infrared remote control codes or creating USB HID actions.

## Features:
* scans available COM/Serial ports until it finds a device that responds with "OK\n" to "AT\n"
* starts a local HTTP server (default port 8080)
* forwards incoming POST request body (plus a newline) to the detected serial device
* supports browser-based POST requests via CORS headers
* automatically rescans if device disconnects

## Requirements:
* pip install pyserial
    
## Usage and optional commandline parameters:
* python http-serial-bridge.py [--http-port <port>] [--baud <baudrate>]
 (http-port: HTTP server port, default: 8080)
 (baud: baudrate for serial connection, default: 115200)

### TBDs and possible improvements:
* linux compatibility and testing
* bidirectional communication and better error handling
* integration with other helper applications (one universal helper application)
* provision of binary executables / user-friendly release

