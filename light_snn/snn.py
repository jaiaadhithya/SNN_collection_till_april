import math
import random
from .memristor import DiscreteMemristor

class SNNController:
    def __init__(self, n_inputs=9, n_hidden=12, n_outputs=4, dt_ms=10.0):
        self.n_inputs = n_inputs
        self.n_hidden = n_hidden
        self.n_outputs = n_outputs
        self.dt_ms = dt_ms
        self.dt = dt_ms / 1000.0
        self.v_spike = 40.0
        self.tau = 0.010
        self.v_threshold = 0.35
        self.v_reset = 0.0
        self.v_hidden = [0.0 for _ in range(n_hidden)]
        self.v_out = [0.0 for _ in range(n_outputs)]
        self.mem_in_hidden = [DiscreteMemristor() for _ in range(n_inputs * n_hidden)]
        self.mem_hidden_out = [DiscreteMemristor() for _ in range(n_hidden * n_outputs)]
        self.max_rate_hz = 50.0
        self.rate_gain = 1.0
        self.train_delta_steps = 8
        self.train_boost = 2
        self.depress_steps = 2
        self.protos = [[0.0 for _ in range(n_inputs)] for _ in range(n_outputs)]
        self.proto_beta = 0.9
        self.proto_gain = 0.6
        self.proto_min_sim = 0.3
        self.choice_idx = None
        self.choice_hold = 0
        self.hold_frames = 5
        self.hold_sim_min = 0.4
        self.switch_margin = 0.1
        self.sim_decide_min = 0.5
        self.sim_decide_margin = 0.1
        self.syn_gain_in = 1.0
        self.syn_gain_out = 1.0
        self.last_drop = [0.0 for _ in range(n_inputs)]
        self.baseline = [0.0 for _ in range(n_inputs)]
        self.dev = [0.0 for _ in range(n_inputs)]
        self.threshold = [0.0 for _ in range(n_inputs)]
        self.sensor_smooth = [0.0 for _ in range(n_inputs)]
        self.last_active_mask = [False for _ in range(n_inputs)]
        self.active_count = [0 for _ in range(n_inputs)]
        self.cal_frames = 0
        self.calibrate_target_frames = 150
        self.noise_margin = 60.0
        self.baseline_beta = 0.95
        self.dev_beta = 0.90
        self.smooth_alpha = 0.2
        self.k_sigma = 0.5
        self.active_frames = 2
        self.flash_margin_extra = 10.0
        self.ratio_min = 0.25
        self.delta_min = 120.0
    def _grid_weights(self, theta, origin, target):
        ox, oy = origin
        tx, ty = target
        denom = math.sqrt((tx - ox) ** 2 + (ty - oy) ** 2) or 1.0
        w = []
        for j in range(3):
            for i in range(3):
                if i == ox and j == oy:
                    val = 0.0
                else:
                    num = (i - ox + 1) * (j - oy + 1)
                    val = theta + math.exp(num / denom)
                w.append(val)
        return w
    def initialize_weights(self, theta=0.0):
        origins = [(0, 0)]
        base_positions = [(0,0),(1,0),(2,0),(0,1),(1,1),(2,1),(0,2),(1,2),(2,2)]
        mats = []
        for k in range(self.n_hidden):
            t = base_positions[k % len(base_positions)]
            mats.append(self._grid_weights(theta, origins[0], t))
        flat = [x for m in mats for x in m]
        if flat:
            mn = min(flat)
            mx = max(flat)
            scale = (self.mem_in_hidden[0].g_max - self.mem_in_hidden[0].g_min) / (mx - mn or 1.0)
            for h in range(min(self.n_hidden, len(mats))):
                for i in range(self.n_inputs):
                    g = self.mem_in_hidden[0].g_min + (mats[h][i] - mn) * scale
                    self.mem_in_hidden[i * self.n_hidden + h].set_conductance(g)
        targets_out = [(0, 1), (2, 1), (1, 2), (1, 0)]
        mats_o = [self._grid_weights(theta, origins[0], t) for t in targets_out]
        flat_o = [x for m in mats_o for x in m]
        if flat_o:
            mn = min(flat_o)
            mx = max(flat_o)
            scale = (self.mem_hidden_out[0].g_max - self.mem_hidden_out[0].g_min) / (mx - mn or 1.0)
            for j in range(self.n_outputs):
                for h in range(min(self.n_hidden, self.n_inputs)):
                    idx = (h % self.n_inputs)
                    g = self.mem_hidden_out[0].g_min + (mats_o[j][idx] - mn) * scale
                    self.mem_hidden_out[h * self.n_outputs + j].set_conductance(g)
    def _spikes_from_sensors(self, sensors, calibrate=False):
        spikes = [False] * self.n_inputs
        for i in range(self.n_inputs):
            x = max(0, min(4095, sensors[i]))
            s = self.sensor_smooth[i]
            self.sensor_smooth[i] = self.smooth_alpha * s + (1.0 - self.smooth_alpha) * x
            if calibrate:
                b = self.baseline[i]
                self.baseline[i] = self.baseline_beta * b + (1.0 - self.baseline_beta) * self.sensor_smooth[i]
                d = self.dev[i]
                self.dev[i] = self.dev_beta * d + (1.0 - self.dev_beta) * abs(self.sensor_smooth[i] - self.baseline[i])
                spikes[i] = False
                self.last_active_mask[i] = False
                self.last_drop[i] = 0.0
                continue
            m = self.noise_margin + self.k_sigma * self.dev[i]
            x_drop = self.baseline[i] - self.sensor_smooth[i] - m
            denom = max(1.0, self.baseline[i])
            self.last_drop[i] = max(0.0, x_drop / denom)
            rel_ok = (self.baseline[i] > 0.0) and (self.sensor_smooth[i] <= self.baseline[i] * (1.0 - self.ratio_min))
            abs_ok = (self.baseline[i] - self.sensor_smooth[i]) >= (self.delta_min + self.k_sigma * self.dev[i])
            if x_drop > 0:
                self.active_count[i] = min(self.active_count[i] + 1, 255)
            else:
                self.active_count[i] = 0
            is_active = (self.active_count[i] >= self.active_frames) and (x_drop > self.flash_margin_extra) and rel_ok and abs_ok
            self.last_active_mask[i] = is_active
            if is_active:
                r = self.max_rate_hz * self.rate_gain * max(0.0, min(1.0, x_drop / denom))
                p = max(0.0, min(1.0, r * self.dt))
                spikes[i] = random.random() < p
            else:
                spikes[i] = False
        if calibrate:
            self.cal_frames += 1
        return spikes
    def _i_syn_in_hidden(self, pre_spikes):
        currents = [0.0] * self.n_hidden
        for i in range(self.n_inputs):
            if pre_spikes[i]:
                for h in range(self.n_hidden):
                    g = self.mem_in_hidden[i * self.n_hidden + h].get_conductance()
                    currents[h] += g * self.v_spike * self.syn_gain_in
        return currents
    def _lif_step_hidden(self, currents):
        spikes = [False] * self.n_hidden
        for h in range(self.n_hidden):
            dv = (currents[h] - self.v_hidden[h]) * (self.dt / self.tau)
            self.v_hidden[h] += dv
            if self.v_hidden[h] > self.v_threshold:
                spikes[h] = True
                self.v_hidden[h] = self.v_reset
        return spikes
    def _i_syn_hidden_out(self, hidden_spikes):
        currents = [0.0] * self.n_outputs
        for h in range(self.n_hidden):
            if hidden_spikes[h]:
                for j in range(self.n_outputs):
                    g = self.mem_hidden_out[h * self.n_outputs + j].get_conductance()
                    currents[j] += g * self.v_spike * self.syn_gain_out
        return currents
    def _lif_step_out(self, currents):
        spikes = [False] * self.n_outputs
        for j in range(self.n_outputs):
            dv = (currents[j] - self.v_out[j]) * (self.dt / self.tau)
            self.v_out[j] += dv
            if self.v_out[j] > self.v_threshold:
                spikes[j] = True
                self.v_out[j] = self.v_reset
        return spikes
    def _dir_index(self, name):
        m = {"left": 0, "right": 1, "front": 2, "back": 3}
        return m.get(name, None)
    def train(self, pre_spikes, hidden_spikes, direction):
        idx = self._dir_index(direction)
        if idx is None:
            return
        for h in range(self.n_hidden):
            if hidden_spikes[h]:
                self.mem_hidden_out[h * self.n_outputs + idx].potentiate(self.train_delta_steps * self.train_boost)
                for j in range(self.n_outputs):
                    if j != idx:
                        self.mem_hidden_out[h * self.n_outputs + j].depress(self.depress_steps)
        for i in range(self.n_inputs):
            if pre_spikes[i]:
                for h in range(self.n_hidden):
                    if hidden_spikes[h]:
                        self.mem_in_hidden[i * self.n_hidden + h].potentiate(self.train_delta_steps * self.train_boost)
        # Update prototype for the selected direction using current drop vector
        for i in range(self.n_inputs):
            p_old = self.protos[idx][i]
            p_new = self.proto_beta * p_old + (1.0 - self.proto_beta) * self.last_drop[i]
            self.protos[idx][i] = p_new
    def step(self, sensors, training=False, train_dir=None, calibrate=False):
        pre_spikes = self._spikes_from_sensors(sensors, calibrate=calibrate)
        hid_curr = self._i_syn_in_hidden(pre_spikes)
        hid_spikes = self._lif_step_hidden(hid_curr)
        if training and train_dir:
            self.train(pre_spikes, hid_spikes, train_dir)
        out_curr = self._i_syn_hidden_out(hid_spikes)
        out_spikes = self._lif_step_out(out_curr)
        if training and train_dir:
            idx_tf = self._dir_index(train_dir)
            if idx_tf is not None:
                out_spikes[idx_tf] = True
        drops = self.last_drop
        norm_d = math.sqrt(sum(d*d for d in drops)) or 1.0
        sims = [0.0] * self.n_outputs
        for j in range(self.n_outputs):
            proto = self.protos[j]
            norm_p = math.sqrt(sum(p*p for p in proto)) or 1.0
            sim = sum(proto[i] * drops[i] for i in range(self.n_inputs)) / (norm_p * norm_d)
            sims[j] = sim
            if sim >= self.proto_min_sim:
                self.v_out[j] += self.proto_gain * sim
        best_idx = max(range(self.n_outputs), key=lambda k: sims[k])
        if not training and not calibrate:
            j = best_idx
            out_spikes = [False] * self.n_outputs
            out_spikes[j] = True
            self.choice_idx = j
            self.choice_hold = self.hold_frames
        else:
            if any(out_spikes):
                j = out_spikes.index(True)
            else:
                j = max(range(self.n_outputs), key=lambda k: self.v_out[k])
        dirs = ["LEFT", "RIGHT", "FRONT", "BACK"]
        return dirs[j], out_spikes, list(self.v_out), hid_spikes, pre_spikes, list(self.v_hidden), list(self.last_active_mask)
