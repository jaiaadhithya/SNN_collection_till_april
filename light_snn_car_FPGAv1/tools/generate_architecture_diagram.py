import pathlib

import matplotlib

matplotlib.use("Agg")

import argparse
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


def _box(ax, xy, w, h, title, lines, fc="#121826", ec="#A7B0C0"):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.5,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h - 0.06 * h,
        title,
        ha="center",
        va="top",
        fontsize=12,
        color="white",
        fontweight="bold",
    )
    if lines:
        ax.text(
            x + 0.04 * w,
            y + h - 0.22 * h,
            "\n".join(lines),
            ha="left",
            va="top",
            fontsize=10,
            color="#D7DCE6",
            family="monospace",
        )
    return patch


def _arrow(ax, p0, p1, text=None, color="#7DD3FC"):
    a = FancyArrowPatch(
        p0,
        p1,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=2.0,
        color=color,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(a)
    if text:
        mx = (p0[0] + p1[0]) / 2
        my = (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.02, text, ha="center", va="bottom", fontsize=9, color="#E5E7EB")
    return a


def _sensor_grid(ax, x, y, size, active=(0, 1, 3, 4)):
    cell = size / 3
    for r in range(3):
        for c in range(3):
            idx = r * 3 + c
            fc = "#0B1220"
            ec = "#334155"
            if idx in active:
                fc = "#1F6FEB"
                ec = "#93C5FD"
            rect = Rectangle((x + c * cell, y + (2 - r) * cell), cell, cell, facecolor=fc, edgecolor=ec, linewidth=1.2)
            ax.add_patch(rect)
    ax.text(x + size / 2, y - 0.03, "3×3 physical grid\n(top 4 used = 2×2)", ha="center", va="top", fontsize=9, color="#D7DCE6")


def render(out_dir: pathlib.Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 7), dpi=160)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("#0B1020")
    ax.set_facecolor("#0B1020")

    ax.text(
        0.5,
        0.97,
        "FPGA SNN Car Architecture (Memristor-Modeled, On-Chip Learning)",
        ha="center",
        va="top",
        fontsize=16,
        color="white",
        fontweight="bold",
    )

    _sensor_grid(ax, x=0.04, y=0.52, size=0.18, active=(0, 1, 3, 4))
    sensors = _box(
        ax,
        (0.03, 0.18),
        0.20,
        0.28,
        "Sensors",
        [
            "LDR voltage dividers",
            "Analog -> Arduino A0–A3",
            "2×2 used (top of 3×3)",
        ],
        fc="#111827",
        ec="#93C5FD",
    )

    arduino = _box(
        ax,
        (0.28, 0.22),
        0.20,
        0.56,
        "Arduino Mega",
        [
            "Sample sensors @ ~100 Hz",
            "Read TRAIN + DIR buttons",
            "Frame: AA 55 09 ... XOR",
            "UART @ 115200",
        ],
        fc="#0F172A",
        ec="#A7F3D0",
    )

    shifter = _box(
        ax,
        (0.52, 0.37),
        0.14,
        0.26,
        "Level Shifter",
        [
            "5V <-> 3.3V",
            "UART RX/TX",
        ],
        fc="#0F172A",
        ec="#FDE68A",
    )

    fpga = _box(
        ax,
        (0.70, 0.10),
        0.27,
        0.80,
        "DE10-Lite FPGA",
        [
            "UART RX -> frame parser",
            "SNN core (hidden+output)",
            "On-chip learning",
            "UART TX telemetry",
            "dir_bits -> LEDs/motor",
        ],
        fc="#111827",
        ec="#FCA5A5",
    )

    _box(
        ax,
        (0.72, 0.67),
        0.23,
        0.18,
        "UART RX + Frame RX",
        [
            "Oversample UART",
            "Verify checksum",
            "Emit frame_valid",
        ],
        fc="#0B1220",
        ec="#93C5FD",
    )

    _box(
        ax,
        (0.72, 0.39),
        0.23,
        0.22,
        "SNN Core",
        [
            "Hidden: 32 LIF neurons",
            "Output: 4 LIF neurons",
            "Multi-output for corners",
        ],
        fc="#0B1220",
        ec="#A7F3D0",
    )

    _box(
        ax,
        (0.72, 0.14),
        0.23,
        0.20,
        "Memristor-Modeled Weights",
        [
            "G_io: sensor -> output",
            "G: hidden -> output",
            "Bounded conductance",
            "Potentiate / depress",
        ],
        fc="#0B1220",
        ec="#FDE68A",
    )

    dashboard = _box(
        ax,
        (0.03, 0.05),
        0.30,
        0.10,
        "Dashboard (PC)",
        [
            "Live spikes + potentials",
            "Proof of on-chip learning",
        ],
        fc="#0F172A",
        ec="#C4B5FD",
    )

    _arrow(ax, (0.23, 0.45), (0.28, 0.45), "A0–A3 + buttons", color="#93C5FD")
    _arrow(ax, (0.48, 0.50), (0.52, 0.50), "UART 115200", color="#A7F3D0")
    _arrow(ax, (0.66, 0.50), (0.70, 0.50), "3.3V UART", color="#FDE68A")
    _arrow(ax, (0.70, 0.30), (0.61, 0.13), "Telemetry (0xBB packets)", color="#C4B5FD")
    _arrow(ax, (0.72, 0.28), (0.94, 0.28), "dir_bits -> LEDs / motor", color="#FCA5A5")

    ax.text(
        0.55,
        0.90,
        "Crossbar idea:\ninputs × conductances → sums",
        ha="center",
        va="center",
        fontsize=10,
        color="#D7DCE6",
    )

    png_path = out_dir / "architecture_overview.png"
    svg_path = out_dir / "architecture_overview.svg"
    fig.savefig(png_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(svg_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return png_path, svg_path


def render_topology(out_dir: pathlib.Path, n_in: int = 4, n_h: int = 28, n_out: int = 4):
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 7), dpi=180)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.text(
        0.5,
        0.96,
        f"SNN Topology ( {n_in} Inputs → {n_h} Hidden LIF Neurons → {n_out} Outputs )",
        ha="center",
        va="top",
        fontsize=18,
        color="#0F172A",
        fontweight="bold",
    )

    x_in = 0.12
    x_h = 0.50
    x_out = 0.88
    y_top = 0.82
    y_bot = 0.18

    def _ys(count: int):
        if count == 1:
            return [0.5]
        step = (y_top - y_bot) / (count - 1)
        return [y_top - i * step for i in range(count)]

    in_labels = ["LDR 1", "LDR 2", "LDR 3", "LDR 4"][:n_in]
    out_labels = ["LEFT", "RIGHT", "FRONT", "CENTER"][:n_out]

    in_pos = [(x_in, y) for y in _ys(n_in)]
    out_pos = [(x_out, y) for y in _ys(n_out)]

    h_pos = [(x_h, y) for y in _ys(n_h)]

    ax.text(x_in, 0.90, "Input Layer", ha="center", va="center", fontsize=12, color="#1D4ED8", fontweight="bold")
    ax.text(x_h, 0.90, "Hidden Layer (28 LIF)", ha="center", va="center", fontsize=12, color="#047857", fontweight="bold")
    ax.text(x_out, 0.90, "Output Layer (4 LIF)", ha="center", va="center", fontsize=12, color="#B91C1C", fontweight="bold")

    def _node(ax, x, y, r, edge, fill, label, label_dx=0.02, label_ha="left"):
        ax.add_patch(Circle((x, y), r, facecolor=fill, edgecolor=edge, linewidth=1.5))
        ax.text(x + label_dx, y, label, ha=label_ha, va="center", fontsize=10, color="#0F172A")

    for (x, y), lab in zip(in_pos, in_labels):
        _node(ax, x, y, 0.020, edge="#1D4ED8", fill="white", label=lab)

    for idx, (x, y) in enumerate(h_pos):
        ax.add_patch(Circle((x, y), 0.0105, facecolor="white", edgecolor="#047857", linewidth=1.2))
        ax.text(x, y, f"H{idx+1}", ha="center", va="center", fontsize=6.0, color="#0F172A")

    for (x, y), lab in zip(out_pos, out_labels):
        _node(ax, x, y, 0.020, edge="#B91C1C", fill="white", label=lab, label_dx=-0.02, label_ha="right")

    wire_color = "#94A3B8"
    for (xi, yi) in in_pos:
        for (xh, yh) in h_pos:
            ax.plot([xi + 0.018, xh - 0.010], [yi, yh], color=wire_color, linewidth=0.35, alpha=0.55)

    for (xh, yh) in h_pos:
        for (xo, yo) in out_pos:
            ax.plot([xh + 0.010, xo - 0.018], [yh, yo], color=wire_color, linewidth=0.35, alpha=0.55)

    ax.text(
        0.5,
        0.06,
        "Fully connected layers; synaptic weights modeled as bounded memristor conductances (potentiate / depress)",
        ha="center",
        va="center",
        fontsize=10,
        color="#334155",
    )

    png_path = out_dir / "snn_topology_4_28_4.png"
    svg_path = out_dir / "snn_topology_4_28_4.svg"
    fig.savefig(png_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(svg_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return png_path, svg_path


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve()
    project_root = here.parents[1]
    out = project_root / "docs"
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Generate the full system architecture overview diagram.")
    args = parser.parse_args()

    if args.full:
        p_png, p_svg = render(out)
    else:
        p_png, p_svg = render_topology(out, n_in=4, n_h=28, n_out=4)

    print(str(p_png))
    print(str(p_svg))
