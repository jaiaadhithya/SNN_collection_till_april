import serial
import serial.tools.list_ports
import time

def debug_serial():
    print("--- Searching for Arduino ---")
    ports = list(serial.tools.list_ports.comports())
    arduino_port = None
    
    for p in ports:
        print(f"Found port: {p.device} - {p.description}")
        if "Arduino" in p.description or "USB Serial" in p.description or "CH340" in p.description:
            arduino_port = p.device
            
    if not arduino_port:
        print("\nERROR: No Arduino found!")
        print("Please check your USB connection.")
        return

    print(f"\nConnecting to {arduino_port} at 115200 baud...")
    
    try:
        ser = serial.Serial(arduino_port, 115200, timeout=1)
        print("Connected! Sending Dummy Data (AA 55 ...) & Listening... (Press Ctrl+C to stop)")
        print("-" * 40)
        
        last_tx = 0
        
        while True:
            # SEND DUMMY DATA every 0.5s to wake up FPGA
            if time.time() - last_tx > 0.5:
                # 0xAA 0x55 [0x09] [Data...] [Checksum]
                # Dummy packet: AA 55 09 01 02 03 04 05 06 07 08 00 [Checksum]
                dummy_pkt = bytes([0xAA, 0x55, 0x09, 
                                   0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x00, 
                                   0x01^0x02^0x03^0x04^0x05^0x06^0x07^0x08^0x00])
                ser.write(dummy_pkt)
                print(f"TX: {dummy_pkt.hex().upper()}")
                last_tx = time.time()

            if ser.in_waiting:
                # Read a chunk of data
                data = ser.read(ser.in_waiting)
                
                # Print hex representation
                hex_str = " ".join([f"{b:02X}" for b in data])
                print(f"RX: {hex_str}")
                
                # specific check for our headers
                if b'\xAA\x55' in data:
                    print("  -> Saw FPGA Packet Header (AA 55) - Loopback?")
                if b'\xCC\xDD' in data:
                    print("  -> Saw Arduino Debug Packet (CC DD) - Arduino is ALIVE")
                if b'\xBB' in data:
                    print("  -> Saw FPGA Output Header (BB) - FPGA is TALKING")
                    
            time.sleep(0.1)
            
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    debug_serial()
