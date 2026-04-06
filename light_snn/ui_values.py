import pygame

class ValuesUI:
    def __init__(self, width=720, height=540, fullscreen=False, n_hidden=12, n_outputs=4):
        self.w = width
        self.h = height
        self.n_hidden = n_hidden
        self.n_outputs = n_outputs
        pygame.init()
        if fullscreen:
            info = pygame.display.Info()
            self.w = info.current_w
            self.h = info.current_h
            self.screen = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN)
            self.fullscreen = True
        else:
            self.screen = pygame.display.set_mode((self.w, self.h))
            self.fullscreen = False
        pygame.display.set_caption("Sensor Values")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small = pygame.font.SysFont(None, 24)
        self.pulse = [0] * 9
        self.pulse_hidden = [0] * self.n_hidden
        self.pulse_out = [0] * self.n_outputs
        self.pulse_in = [0] * 9
    def toggle_fullscreen(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode((720, 540))
            self.w, self.h = 720, 540
            self.fullscreen = False
        else:
            info = pygame.display.Info()
            self.w = info.current_w
            self.h = info.current_h
            self.screen = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN)
            self.fullscreen = True
    def update(self, sensors, buttons, spikes=None, active_mask=None, hidden_spikes=None, out_spikes=None, v_hidden=None, v_out=None, direction=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_f, pygame.K_F11):
                    self.toggle_fullscreen()
        self.screen.fill((15, 15, 25))
        margin = 20
        grid_w = (self.w // 2) - 2 * margin
        grid_h = self.h - 2 * margin
        size = min(grid_w, grid_h)
        cell = size // 3
        left = margin
        top = (self.h - size) // 2
        for j in range(3):
            for i in range(3):
                idx = j * 3 + i
                x = left + i * cell
                y = top + j * cell
                rect = pygame.Rect(x, y, cell - 8, cell - 8)
                base = (40, 50, 70)
                hl = (230, 230, 90)
                fill = base
                if active_mask and idx < len(active_mask) and active_mask[idx]:
                    fill = hl
                pygame.draw.rect(self.screen, fill, rect)
                border = 2
                if active_mask and idx < len(active_mask) and active_mask[idx]:
                    pygame.draw.rect(self.screen, (200, 230, 200), rect, 2)
                else:
                    pygame.draw.rect(self.screen, (200, 200, 220), rect, 2)
                val = sensors[idx] if idx < len(sensors) else 0
                text = self.font.render(str(val), True, (240, 240, 240))
                tx = rect.x + rect.width // 2 - text.get_width() // 2
                ty = rect.y + rect.height // 2 - text.get_height() // 2
                self.screen.blit(text, (tx, ty))
                if spikes and idx < len(spikes) and spikes[idx]:
                    self.pulse[idx] = max(self.pulse[idx], 8)
                p = self.pulse[idx]
                if p > 0:
                    w = min(6, 2 + p)
                    pygame.draw.rect(self.screen, hl, rect, w)
                    self.pulse[idx] -= 1
        # Right side simple network diagram
        right_left = self.w // 2
        area_w = self.w // 2 - 2 * margin
        area_h = self.h - 2 * margin
        hidden_pos = []
        for h_idx in range(self.n_hidden):
            x = right_left + margin + int(area_w * 0.40)
            y = margin + int((h_idx + 0.5) * area_h / self.n_hidden)
            hidden_pos.append((x, y))
        input_pos = []
        cell_h = area_h // 3
        cell_w = max(22, int(area_w * 0.25) // 3)
        start_x = right_left + margin + int(area_w * 0.10)
        start_y = margin + (area_h - 3 * cell_h) // 2
        for j in range(3):
            for i in range(3):
                x = start_x + i * (cell_w + 8)
                y = start_y + j * cell_h + cell_h // 2
                input_pos.append((x, y))
        out_pos = []
        for j in range(self.n_outputs):
            x = right_left + margin + int(area_w * 0.75)
            y = margin + int((j + 0.5) * area_h / self.n_outputs)
            out_pos.append((x, y))
        for h_idx in range(self.n_hidden):
            p = self.pulse_hidden[h_idx]
            base = (120, 160, 255)
            glow = (180, 200, 255)
            radius = 10
            pygame.draw.circle(self.screen, base, hidden_pos[h_idx], radius)
            if hidden_spikes and h_idx < len(hidden_spikes) and hidden_spikes[h_idx]:
                self.pulse_hidden[h_idx] = 8
            if p > 0:
                pygame.draw.circle(self.screen, glow, hidden_pos[h_idx], radius + p)
                self.pulse_hidden[h_idx] -= 1
        labels_o = ["LEFT","RIGHT","FRONT","BACK"]
        for j in range(self.n_outputs):
            p = self.pulse_out[j]
            base = (60, 200, 120)
            glow = (120, 255, 180)
            radius = 12
            pygame.draw.circle(self.screen, base, out_pos[j], radius)
            txt = self.small.render(labels_o[j], True, (230, 230, 230))
            self.screen.blit(txt, (out_pos[j][0] - 30, out_pos[j][1] - 30))
            if out_spikes and j < len(out_spikes) and out_spikes[j]:
                self.pulse_out[j] = 10
            if p > 0:
                pygame.draw.circle(self.screen, glow, out_pos[j], radius + p)
                self.pulse_out[j] -= 1
        labels = ["train","left","right","front","back"]
        mask_show = []
        for k in labels:
            v = 1 if buttons.get(k, False) else 0
            mask_show.append(f"{k}:{v}")
        info = "  ".join(mask_show)
        info_surf = self.small.render(info, True, (220, 220, 230))
        self.screen.blit(info_surf, (margin, self.h - margin - info_surf.get_height()))
        for i in range(9):
            p = self.pulse_in[i]
            base = (200, 200, 220)
            glow = (240, 240, 160)
            radius = 8
            pygame.draw.circle(self.screen, base, input_pos[i], radius)
            if spikes and i < len(spikes) and spikes[i]:
                self.pulse_in[i] = 6
            if p > 0:
                pygame.draw.circle(self.screen, glow, input_pos[i], radius + p)
                self.pulse_in[i] -= 1
        if direction:
            dir_surf = self.small.render(str(direction), True, (240, 240, 240))
            self.screen.blit(dir_surf, (right_left + margin, self.h - margin - dir_surf.get_height()))
        pygame.display.flip()
        self.clock.tick(60)
