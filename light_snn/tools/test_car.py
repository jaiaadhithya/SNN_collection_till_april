import argparse
import time
from light_snn.io_wifi import Esp32Client

def move(client, direction, power, duration):
    client.send_direction(direction, power=power)
    time.sleep(duration)
    client.stop()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--esp32_host", required=True)
    p.add_argument("--esp32_port", type=int, default=12345)
    p.add_argument("--power", type=float, default=0.5)
    p.add_argument("--step_s", type=float, default=1.0)
    p.add_argument("--pause_s", type=float, default=0.5)
    p.add_argument("--sequence", default="forward,stop,back,stop,left,stop,right,stop")
    args = p.parse_args()
    cl = Esp32Client(args.esp32_host, args.esp32_port)
    parts = [x.strip().lower() for x in args.sequence.split(",") if x.strip()]
    for cmd in parts:
        if cmd == "forward":
            move(cl, "FRONT", args.power, args.step_s)
        elif cmd == "back":
            move(cl, "BACK", args.power, args.step_s)
        elif cmd == "left":
            move(cl, "LEFT", args.power, args.step_s)
        elif cmd == "right":
            move(cl, "RIGHT", args.power, args.step_s)
        elif cmd == "stop":
            cl.stop()
            time.sleep(args.pause_s)
        elif cmd == "curve_left":
            cl.send_direction("LEFT", power=args.power * 0.5)
            cl.send_direction("FRONT", power=args.power)
            time.sleep(args.step_s)
            cl.stop()
        elif cmd == "curve_right":
            cl.send_direction("RIGHT", power=args.power * 0.5)
            cl.send_direction("FRONT", power=args.power)
            time.sleep(args.step_s)
            cl.stop()
        else:
            cl.stop()
            time.sleep(args.pause_s)

if __name__ == "__main__":
    main()
