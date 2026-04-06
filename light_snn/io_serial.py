import serial

class SerialReader:
    def __init__(self, port, baud=115200, timeout=0.02, n_inputs=9):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.n_inputs = n_inputs
        self.ser = serial.Serial(port=self.port, baudrate=self.baud, timeout=self.timeout)
    def read_frame(self):
        header = self.ser.read(2)
        if not header or len(header) < 2 or header[0] != 0xAA or header[1] != 0x55:
            return None
        payload_len = self.n_inputs * 2 + 1
        payload = self.ser.read(payload_len)
        if not payload or len(payload) < payload_len:
            return None
        sensors = []
        for k in range(self.n_inputs):
            hi = payload[2 * k]
            lo = payload[2 * k + 1]
            w = (hi << 8) | lo
            sensors.append(w & 0x0FFF)
        mask = payload[-1]
        buttons = {
            "train": bool(mask & 0x01),
            "left": bool(mask & 0x02),
            "right": bool(mask & 0x04),
            "front": bool(mask & 0x08),
            "back": bool(mask & 0x10),
        }
        return sensors, buttons
