class DiscreteMemristor:
    def __init__(self, n_states=256, g_min=1e-6, g_max=1e-4):
        self.n_states = n_states
        self.state = n_states // 2
        self.g_min = g_min
        self.g_max = g_max
    def get_conductance(self):
        w = self.state / (self.n_states - 1)
        return self.g_min * (1 - w) + self.g_max * w
    def potentiate(self, steps=1):
        self.state = min(self.state + steps, self.n_states - 1)
    def depress(self, steps=1):
        self.state = max(self.state - steps, 0)
    def set_conductance(self, g):
        g = max(self.g_min, min(self.g_max, g))
        w = (g - self.g_min) / (self.g_max - self.g_min)
        self.state = int(round(w * (self.n_states - 1)))

