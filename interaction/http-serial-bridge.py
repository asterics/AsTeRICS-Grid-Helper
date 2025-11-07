#!/usr/bin/env python3
"""
AsTeRICS Grid Helper HTTP-to-Serial Bridge
------------------------------------------
This helper application for AsTeRICS Grid provides a local webserver which forwards AT commands to a connected FABI or FlipMouse device. 
It automatically connects to the first compatible device found via scanning the available COM/Serial ports.

Features:
- scans available COM/Serial ports until it finds a device that responds with "OK\n" to "AT\n"
- starts a local HTTP server (default port 8080)
- forwards incoming POST request body (plus a newline) to the detected serial device
- supports browser-based POST requests via CORS headers
- automatically rescans if device disconnects

Requirements:
    pip install pyserial
    
Usage and optional commandline parameters:
    python http-serial-bridge.py [--http-port <port>] [--baud <baudrate>]
    (http-port: HTTP server port, default: 8080)
    (baud: baudrate for serial connection, default: 115200)

TBDs and possible improvements:
- linux compatibility and testing
- bidirectional communication and better error handling
- integration with other helper applications (one universal helper application)
- provision of binary executables / user-friendly release

"""

import argparse
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import serial
import serial.tools.list_ports
import multiprocessing
from multiprocessing import Pipe
import traceback
from typing import Optional

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
DEFAULT_BAUDRATE = 115200
DEFAULT_HTTP_PORT = 8080
AT_COMMAND = b"AT\n"
EXPECTED_RESPONSE = b"OK\n"

PER_PORT_RESPONSE_TIMEOUT = 1.0   # seconds waiting for "OK\n"
OPEN_TIMEOUT = 1.0                # absolute per-port open timeout (process kill)
PORT_SCAN_DELAY = 0.5             # delay between scan passes

SKIP_PATTERNS = ["Bluetooth", "BTHENUM", "RFCOMM", "BlueSoleil"]  # skip known Bluetooth COM ports which might block the scanning process

# Shared globals
_serial_lock = threading.RLock()
_serial_instance: Optional[serial.Serial] = None
_stop_event = threading.Event()

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# -------------------------------------------------------------------
# Utility functions for port testing
# -------------------------------------------------------------------
def port_looks_like_bluetooth(port_info) -> bool:
    """Heuristic to skip known virtual/Bluetooth ports"""
    txt = " ".join(
        filter(None, [getattr(port_info, "description", ""),
                      getattr(port_info, "hwid", ""),
                      getattr(port_info, "manufacturer", "")])
    ).lower()
    return any(pat.lower() in txt for pat in SKIP_PATTERNS)


def _port_test_worker(conn, port_name, baudrate, at_command, expected_response, read_timeout):
    """Runs in a subprocess to test a single COM port safely"""
    try:
        ser = serial.Serial(port=port_name, baudrate=baudrate, timeout=read_timeout)
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            ser.write(at_command)
            ser.flush()
            resp = ser.readline()
            ser.close()
            if resp == expected_response or (resp and resp.strip() == expected_response.strip()):
                conn.send((True, f"OK on {port_name}"))
            else:
                conn.send((False, f"No valid resp on {port_name}: {resp!r}"))
        except Exception as e:
            try:
                ser.close()
            except Exception:
                pass
            conn.send((False, f"Comm error on {port_name}: {e}"))
    except Exception as e:
        conn.send((False, f"Open failed on {port_name}: {e}\n{traceback.format_exc()}"))
    finally:
        conn.close()


def try_port_with_timeout(port_name, baudrate, at_command, expected_response,
                          per_port_response_timeout, open_timeout):
    """Run _port_test_worker in a subprocess and kill if it hangs"""
    parent_conn, child_conn = Pipe(duplex=False)
    p = multiprocessing.Process(
        target=_port_test_worker,
        args=(child_conn, port_name, baudrate, at_command, expected_response, per_port_response_timeout),
        daemon=True,
    )
    p.start()
    child_conn.close()
    p.join(open_timeout)
    if p.is_alive():
        p.terminate()
        p.join(0.2)
        return False, f"Timeout opening {port_name}"
    if parent_conn.poll(0.1):
        success, msg = parent_conn.recv()
        return success, msg
    return False, f"No result for {port_name}"


# -------------------------------------------------------------------
# Serial scanner thread
# -------------------------------------------------------------------
def serial_scanner(baudrate: int):
    global _serial_instance

    logging.info("Serial scanner thread started (baud=%d).", baudrate)
    while not _stop_event.is_set():
        # Skip scanning if we already have a connected serial port
        with _serial_lock:
            ser = _serial_instance
        if ser is not None and ser.is_open:
            time.sleep(0.3)
            continue

        ports = list(serial.tools.list_ports.comports())
        if not ports:
            logging.debug("No COM ports detected; retrying soon.")
            time.sleep(PORT_SCAN_DELAY)
            continue

        for p in ports:
            if _stop_event.is_set():
                break
            port_name = p.device

            if port_looks_like_bluetooth(p):
                logging.info("Skipping likely Bluetooth/virtual port %s", port_name)
                continue

            logging.info("Testing port %s ...", port_name)
            success, msg = try_port_with_timeout(
                port_name, baudrate, AT_COMMAND, EXPECTED_RESPONSE,
                PER_PORT_RESPONSE_TIMEOUT, OPEN_TIMEOUT
            )
            logging.debug(msg)

            if success:
                try:
                    ser = serial.Serial(port=port_name, baudrate=baudrate, timeout=None)
                    with _serial_lock:
                        _serial_instance = ser
                    logging.info("Device detected and connected on %s", port_name)
                    break
                except Exception as e:
                    logging.warning("Failed to open %s for persistent use: %s", port_name, e)

        with _serial_lock:
            if _serial_instance is None:
                time.sleep(PORT_SCAN_DELAY)

    logging.info("Serial scanner thread exiting.")


# -------------------------------------------------------------------
# HTTP request handler
# -------------------------------------------------------------------
class COMBridgeHandler(BaseHTTPRequestHandler):
    server_version = "COMBridgeHTTP/1.0"

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        global _serial_instance
        content_length = int(self.headers.get("Content-Length", "0"))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            body_text = body_bytes.decode("utf-8").rstrip("\r\n")
        except Exception:
            body_text = None

        with _serial_lock:
            ser = _serial_instance

        if ser is None or not ser.is_open:
            self.send_response(503, "Service Unavailable")
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Device not detected yet. Try again later.\n")
            logging.info("POST received but device not available; returned 503.")
            return

        try:
            # Add newline and send to COM port
            to_send = (body_text + "\n").encode("utf-8") if body_text is not None else body_bytes + b"\n"
            ser.write(to_send)
            ser.flush()

            print(f"Sent to device on {ser.port}: {to_send!r}")
            logging.info("Forwarded POST body (%d bytes) to device on %s", len(to_send), ser.port)

            self.send_response(200, "OK")
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Sent to device\n")

        except Exception as e:
            logging.error("Failed to write to serial device: %s", e)
            with _serial_lock:
                try:
                    ser.close()
                except Exception:
                    pass
                _serial_instance = None
            self.send_response(500, "Internal Server Error")
            self._set_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Failed to write to device\n")

    def do_GET(self):
        global _serial_instance
        with _serial_lock:
            ser = _serial_instance
        self.send_response(200, "OK")
        self._set_cors_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        msg = f"Device connected on {ser.port}\n" if ser and ser.is_open else "Device not connected\n"
        self.wfile.write(msg.encode("utf-8"))

    def log_message(self, format, *args):
        logging.info("%s - - %s", self.client_address[0], format % args)


# -------------------------------------------------------------------
# Server entrypoint
# -------------------------------------------------------------------
def run_server(http_port: int, baudrate: int):
    scanner_thread = threading.Thread(target=serial_scanner, args=(baudrate,), daemon=True)
    scanner_thread.start()

    server_address = ("", http_port)
    httpd = ThreadingHTTPServer(server_address, COMBridgeHandler)
    logging.info("HTTP server running on port %d. POST bodies will be forwarded to device once detected.", http_port)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down...")
    finally:
        _stop_event.set()
        httpd.shutdown()
        httpd.server_close()
        with _serial_lock:
            global _serial_instance
            if _serial_instance:
                try:
                    _serial_instance.close()
                except Exception:
                    pass
                _serial_instance = None
        logging.info("Server stopped.")


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="http-serial-bridge.py: a HTTP-to-Serial bridge for AsTeRICS Grid, FABI and FlipMouse")
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT, help="HTTP server port (default 8080)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUDRATE, help="Serial baud rate (default 115200)")
    args = parser.parse_args()
    run_server(http_port=args.http_port, baudrate=args.baud)

