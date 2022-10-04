# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from urllib.parse import urlparse

import boto3

LISTENER_ADDRESS = "127.0.0.1"
RECEIVER_PORT = 8443


def braket_device_cache_init():
    print("Initializing cache")
    devices = {}
    poller_thread = Thread(target=braket_device_poller, daemon=True, args=(devices,))
    poller_thread.start()

    def handler(*args):
        class BraketDeviceServer(BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    # device = self._devices.get(self.path[1:])
                    # json_to_pass = json.dumps(self._devices)
                    json_to_pass = {"foo": "bar"}

                    self.send_response(code=200)
                    self.send_header(keyword="Content-type", value="application/json")
                    self.end_headers()
                    self.wfile.write(json_to_pass.encode("utf-8"))
                    self.send_response

                except Exception as e:
                    print(f"Error processing message: {e}")

                    json_to_pass = {"error_message": str(e)}
                    self.send_response(code=500)
                    self.send_header(keyword="Content-type", value="application/json")
                    self.end_headers()
                    self.wfile.write(json_to_pass.encode("utf-8"))
                    self.send_response

        return BraketDeviceServer

    print(f"Initializing HTTP Server on {LISTENER_ADDRESS}:{RECEIVER_PORT}")
    server = HTTPServer((LISTENER_ADDRESS, RECEIVER_PORT), handler)
    server_thread = Thread(target=serve, daemon=True, args=(server, RECEIVER_PORT))
    server_thread.start()


def braket_device_poller(devices):
    braket = boto3.client("braket")
    while True:
        try:
            response = braket.search_devices(filters=[])
            for device in response["devices"]:
                devices[device["deviceArn"]] = device

            time.sleep(10)

        except Exception as e:
            print("Error polling", e)


def serve(server, listener_name):
    try:
        print(f"Serving HTTP Server on {listener_name}:{RECEIVER_PORT}")
        server.serve_forever()
    except Exception:
        print(f"Error in HTTP server {sys.exc_info()[0]}")
    finally:
        if server:
            server.shutdown()
