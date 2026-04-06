#!/usr/bin/env python3
import math
import argparse

N_OUT = 2

def build_params(N):
    X0, Y0 = 0, 0
    L = max(1, N - 1)
    denoms = {
        'h': math.sqrt((L - X0)**2 + (0 - Y0)**2),
        'v': math.sqrt((0 - X0)**2 + (L - Y0)**2),
        'd0': math.sqrt((L - X0)**2 + (L - Y0)**2),
        'd1': math.sqrt((L - X0)**2 + (-L - Y0)**2),
    }
    theta_rows = [0.05 + i * (0.5 / max(1, N - 1)) for i in range(N)]
    theta_diag0 = 0.75
    theta_diag1 = 0.95
    return X0, Y0, denoms, theta_rows, theta_diag0, theta_diag1

def grid_coords(N):
    return [(x, y) for y in range(N) for x in range(N)]

EPS_PER_OUTPUT = [0.0, 1e-3]

def classify_line(x, y, N):
    if x == y:
        return 'd0'
    if x + y == (N - 1):
        return 'd1'
    return f'h{y}'

def compute_W(x, y, j, N, X0, Y0, denoms, theta_rows, theta_diag0, theta_diag1):
    if x == 0 and y == 0:
        return 0.0
    tag = classify_line(x, y, N)
    if tag == 'd0':
        theta = theta_diag0
        denom = denoms['d0']
    elif tag == 'd1':
        theta = theta_diag1
        denom = denoms['d0']
    else:
        yidx = int(tag[1:])
        theta = theta_rows[yidx]
        denom = denoms['h']
    numerator = (x + X0 + 1) * (y + Y0 + 1)
    return theta + math.exp(numerator / denom) + EPS_PER_OUTPUT[j]

def normalize_to_u16(values, g_min=0, g_max=65535):
    vmin = min(values)
    vmax = max(values)
    span = vmax - vmin if vmax > vmin else 1.0
    scaled = [int(round(g_min + (v - vmin) * (g_max - g_min) / span)) for v in values]
    used = set()
    unique = []
    for g in scaled:
        while g in used:
            g = min(g + 1, g_max)
        used.add(g)
        unique.append(g)
    return unique

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=3, help='Grid size N (NxN sensors)')
    args = parser.parse_args()
    N = args.size
    N_IN = N * N
    X0, Y0, denoms, theta_rows, theta_diag0, theta_diag1 = build_params(N)
    coords = grid_coords(N)
    W = []
    for (x, y) in coords:
        for j in range(N_OUT):
            W.append(compute_W(x, y, j, N, X0, Y0, denoms, theta_rows, theta_diag0, theta_diag1))
    G = normalize_to_u16(W, g_min=0, g_max=65535)
    with open('weights_rom.hex', 'w') as f:
        for g in G:
            f.write(f"{g:04x}\n")
    print("Generated weights_rom.hex with", len(G), "entries for", N, "x", N, "grid")
    left = G[0::2]
    right= G[1::2]
    print("Left conductances (j=0):")
    for r in range(N):
        row = left[r*N:(r+1)*N]
        print(row)
    print("Right conductances (j=1):")
    for r in range(N):
        row = right[r*N:(r+1)*N]
        print(row)

if __name__ == '__main__':
    main()

