import argparse
import time
from .io_serial import SerialReader
from .io_wifi import Esp32Client
from .snn import SNNController
from .ui_values import ValuesUI

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--serial", required=True)
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--esp32_host", default="127.0.0.1")
    p.add_argument("--esp32_port", type=int, default=12345)
    p.add_argument("--dt_ms", type=float, default=10.0)
    p.add_argument("--n_hidden", type=int, default=12)
    p.add_argument("--init_theta", type=float, default=0.0)
    p.add_argument("--dry_run", action="store_true")
    p.add_argument("--ui", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--ui_values", action="store_true")
    p.add_argument("--fullscreen", action="store_true")
    p.add_argument("--calibrate_frames", type=int, default=200)
    p.add_argument("--noise_margin", type=float, default=200.0)
    p.add_argument("--sigma_multiplier", type=float, default=2.0)
    p.add_argument("--smooth_alpha", type=float, default=0.4)
    p.add_argument("--active_frames", type=int, default=3)
    p.add_argument("--flash_extra", type=float, default=50.0)
    p.add_argument("--ratio_min", type=float, default=0.25)
    p.add_argument("--delta_min", type=float, default=120.0)
    p.add_argument("--max_rate_hz", type=float, default=50.0)
    p.add_argument("--rate_gain", type=float, default=1.0)
    p.add_argument("--v_threshold", type=float, default=0.35)
    p.add_argument("--train_steps", type=int, default=8)
    p.add_argument("--v_spike", type=float, default=40.0)
    p.add_argument("--train_boost", type=int, default=2)
    p.add_argument("--depress_steps", type=int, default=2)
    p.add_argument("--proto_gain", type=float, default=0.6)
    p.add_argument("--proto_min_sim", type=float, default=0.3)
    p.add_argument("--proto_beta", type=float, default=0.9)
    p.add_argument("--hold_frames", type=int, default=5)
    p.add_argument("--hold_sim_min", type=float, default=0.4)
    p.add_argument("--switch_margin", type=float, default=0.1)
    p.add_argument("--sim_decide_min", type=float, default=0.5)
    p.add_argument("--sim_decide_margin", type=float, default=0.1)
    p.add_argument("--syn_gain_in", type=float, default=1.0)
    p.add_argument("--syn_gain_out", type=float, default=1.0)
    args = p.parse_args()
    sr = None if args.demo else SerialReader(args.serial, args.baud, n_inputs=9)
    cl = Esp32Client(args.esp32_host, args.esp32_port)
    snn = SNNController(n_inputs=9, n_hidden=args.n_hidden, n_outputs=4, dt_ms=args.dt_ms)
    snn.calibrate_target_frames = args.calibrate_frames
    snn.noise_margin = args.noise_margin
    snn.k_sigma = args.sigma_multiplier
    snn.smooth_alpha = args.smooth_alpha
    snn.active_frames = args.active_frames
    snn.flash_margin_extra = args.flash_extra
    snn.ratio_min = args.ratio_min
    snn.delta_min = args.delta_min
    snn.max_rate_hz = args.max_rate_hz
    snn.rate_gain = args.rate_gain
    snn.v_threshold = args.v_threshold
    snn.train_delta_steps = args.train_steps
    snn.v_spike = args.v_spike
    snn.train_boost = args.train_boost
    snn.depress_steps = args.depress_steps
    snn.proto_gain = args.proto_gain
    snn.proto_min_sim = args.proto_min_sim
    snn.proto_beta = args.proto_beta
    snn.hold_frames = args.hold_frames
    snn.hold_sim_min = args.hold_sim_min
    snn.switch_margin = args.switch_margin
    snn.sim_decide_min = args.sim_decide_min
    snn.sim_decide_margin = args.sim_decide_margin
    snn.syn_gain_in = args.syn_gain_in
    snn.syn_gain_out = args.syn_gain_out
    snn.initialize_weights(theta=args.init_theta)
    viz = None
    if args.ui_values or args.ui:
        viz = ValuesUI(width=960, height=540, fullscreen=args.fullscreen, n_hidden=args.n_hidden, n_outputs=4)
    t = 0
    sensors = [0] * 9
    while True:
        if args.ui_values or args.ui:
            buttons = {"train":False,"left":False,"right":False,"front":False,"back":False}
            if sr is not None:
                frame = sr.read_frame()
                if frame:
                    sensors, buttons = frame
            training = not bool(buttons.get("train", False))
            train_dir = None
            if not bool(buttons.get("left", False)):
                train_dir = "left"
            elif not bool(buttons.get("right", False)):
                train_dir = "right"
            elif not bool(buttons.get("front", False)):
                train_dir = "front"
            elif not bool(buttons.get("back", False)):
                train_dir = "back"
            calibrate = (snn.cal_frames < snn.calibrate_target_frames) and not training and not args.demo
            rv = snn.step(sensors, training=training, train_dir=train_dir, calibrate=calibrate)
            direction, out_spikes, v_out, hid_spikes, pre_spikes, v_hidden, active_mask = rv
            if viz:
                viz.update(sensors, buttons, pre_spikes, active_mask, hid_spikes, out_spikes, v_hidden, v_out, direction)
            if not training and not args.demo:
                if args.dry_run:
                    pass
                else:
                    if str(direction) == "LEFT":
                        cl.stop()
                    else:
                        cl.send_direction(direction, power=0.6)
            time.sleep(args.dt_ms / 1000.0)
            t += 1
            continue
        if args.demo:
            idx = (t // 10) % 9
            sensors = [400 if i == idx else 40 for i in range(9)]
            training = False
            train_dir = None
        else:
            frame = sr.read_frame()
            if not frame:
                if viz:
                    b = {"train":False,"left":False,"right":False,"front":False,"back":False}
                    viz.update(sensors, b, [False]*9, [False]*9, [False]*args.n_hidden, [False]*4, [0.0]*args.n_hidden, [0.0]*4, None)
                time.sleep(args.dt_ms / 1000.0)
                t += 1
                continue
            sensors, buttons = frame
            training = not bool(buttons.get("train", False))
            train_dir = None
            if not bool(buttons.get("left", False)):
                train_dir = "left"
            elif not bool(buttons.get("right", False)):
                train_dir = "right"
            elif not bool(buttons.get("front", False)):
                train_dir = "front"
            elif not bool(buttons.get("back", False)):
                train_dir = "back"
        calibrate = (snn.cal_frames < snn.calibrate_target_frames) and not training and not args.demo
        rv = snn.step(sensors, training=training, train_dir=train_dir, calibrate=calibrate)
        direction, out_spikes, v_out, hid_spikes, pre_spikes, v_hidden, active_mask = rv
        if viz:
            b = {"train":bool(buttons.get("train", False)),"left":bool(buttons.get("left", False)),"right":bool(buttons.get("right", False)),"front":bool(buttons.get("front", False)),"back":bool(buttons.get("back", False))} if not args.demo else {"train":False,"left":False,"right":False,"front":False,"back":False}
            viz.update(sensors, b, pre_spikes, active_mask, hid_spikes, out_spikes, v_hidden, v_out, direction)
        if not training and not args.demo:
            if args.dry_run:
                pass
            else:
                if str(direction) == "LEFT":
                    cl.stop()
                else:
                    cl.send_direction(direction, power=0.6)
        time.sleep(args.dt_ms / 1000.0)
        t += 1

if __name__ == "__main__":
    main()
