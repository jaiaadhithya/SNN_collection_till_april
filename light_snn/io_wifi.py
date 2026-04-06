import socket
import json

class Esp32Client:
    def __init__(self, host, port=12345):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def send(self, payload):
        data = json.dumps(payload).encode("utf-8")
        self.sock.sendto(data, self.addr)
    def send_direction(self, direction, power=0.5):
        self.send({"cmd": "MOVE", "dir": direction, "power": power})
    def stop(self):
        self.send({"cmd": "STOP"})

