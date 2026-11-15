"""Experiment 3: continuously backlogged source, data-packet errors, no ACK errors.

(a) Fixed Ws = 64 (well above the 11 needed for full error-free utilization),
    sweep pd. GBN (Wr = 1), SR with Wr = 11, 32, 64, and S&W as reference.
    Compared against:
        S&W : 1 / (11 + (1/q - 1) * 16),  q = 1 - pd
        GBN : (1 - pd) / (1 + (K - 1) pd),  K = (T_tx + T_out) / T_tx = 16
        SR  : 1 - pd  (window never stalls)
(b) Fixed pd = 0.1, sweep Ws. Efficiency and mean transmission attempts per
    delivered packet for GBN and SR (Wr = 11, 32, 64, capped at Ws).

Every point is averaged over the 5 shared seeds; error bars are 95 % CIs.

Run from the repo root:  py -3.12 experiments/exp3_packet_errors.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from sim import config, theory  # noqa: E402
from sim.batch import run_points, write_csv  # noqa: E402
from sim.plotting import RESULT_DIR, plt, save  # noqa: E402

WS_A = 64
SR_WR = [11, 32, 64]
PD_VALUES = [0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

PD_B = 0.1
WS_B = [1, 2, 4, 6, 8, 10, 11, 12, 14, 16, 20, 24, 28, 32, 40, 48, 56, 64, 80, 100]

COMMON = dict(sim_time=config.SIM_TIME, warmup=config.WARMUP)


def protocols(Ws, cap_wr=False):
    """(label, Ws, Wr) for GBN and the three SR receive windows."""
    out = [("GBN", Ws, 1)]
    for wr in SR_WR:
        out.append((f"SR Wr={wr}", Ws, min(wr, Ws) if cap_wr else wr))
    return out


def run(pts, labels, csv_name):
    """Run all points over the seeds, tag them, save a CSV, group by label."""
    rows = run_points(pts, **COMMON)
    for r, lab in zip(rows, labels):
        r["label"] = lab
    write_csv(rows, os.path.join(RESULT_DIR, csv_name))
    return {lab: [r for r in rows if r["label"] == lab] for lab in dict.fromkeys(labels)}


def plot_sim(ax, x, rows, key, label, marker):
    """Simulated points: markers only (no connecting lines), 95 % CI error bars."""
    ax.errorbar(x, [r[key] for r in rows], yerr=[r[key + "_ci"] for r in rows],
                ls="none", marker=marker, capsize=3, label=label)


def part_a():
    pts, labels = [], []
    for pd in PD_VALUES:
        pts.append(dict(Ws=1, Wr=1, pd=pd)); labels.append("S&W")
        for lab, ws, wr in protocols(WS_A):
            pts.append(dict(Ws=ws, Wr=wr, pd=pd)); labels.append(lab)
    by = run(pts, labels, "exp3a_efficiency_vs_pd.csv")

    fig, ax = plt.subplots()
    fine = np.linspace(0, 0.9, 200)
    ax.plot(fine, [theory.efficiency_sw(p, 0) for p in fine], "k:", label="S&W analysis")
    ax.plot(fine, [theory.efficiency_gbn(p) for p in fine], "k-.", label="GBN analysis")
    ax.plot(fine, [theory.efficiency_sr(p) for p in fine], "k--", label="SR analysis")
    for lab, marker in zip(["S&W", "GBN"] + [f"SR Wr={w}" for w in SR_WR], "so^vD"):
        plot_sim(ax, PD_VALUES, by[lab], "efficiency", lab, marker)
    ax.set_xlabel("Data-packet error probability $p_d$")
    ax.set_ylabel("Link efficiency")
    ax.set_title(f"Exp 3(a): efficiency vs $p_d$ ($W_s$ = {WS_A}, $p_a$ = 0)")
    ax.legend()
    save(fig, "exp3a_efficiency_vs_pd.png")

    print(f"\n=== Exp 3(a): Ws = {WS_A}, pa = 0 ===")
    hdr = ["S&W", "th", "GBN", "th"] + [f"SR{w}" for w in SR_WR] + ["th SR"]
    print(f"{'pd':>5} " + " ".join(f"{h:>7}" for h in hdr))
    for i, pd in enumerate(PD_VALUES):
        vals = [by["S&W"][i]["efficiency"], theory.efficiency_sw(pd, 0),
                by["GBN"][i]["efficiency"], theory.efficiency_gbn(pd)]
        vals += [by[f"SR Wr={w}"][i]["efficiency"] for w in SR_WR] + [theory.efficiency_sr(pd)]
        print(f"{pd:5.2f} " + " ".join(f"{v:7.4f}" for v in vals))


def part_b():
    pts, labels = [], []
    for ws in WS_B:
        for lab, w, wr in protocols(ws, cap_wr=True):
            pts.append(dict(Ws=w, Wr=wr, pd=PD_B)); labels.append(lab)
    pts.append(dict(Ws=1, Wr=1, pd=PD_B)); labels.append("S&W")
    by = run(pts, labels, "exp3b_vs_ws.csv")
    sw = by["S&W"][0]

    for key, ylabel, fname in [
        ("efficiency", "Link efficiency", "exp3b_efficiency_vs_ws.png"),
        ("attempts_per_packet", "Transmission attempts per delivered packet",
         "exp3b_attempts_vs_ws.png"),
    ]:
        fig, ax = plt.subplots()
        ax.axhline(sw[key], color="k", ls=":", label="S&W")
        for lab, marker in zip(["GBN"] + [f"SR Wr={w}" for w in SR_WR], "o^vD"):
            plot_sim(ax, WS_B, by[lab], key, lab, marker)
        ax.set_xscale("log")
        ax.set_xlabel("Send window size $W_s$ (packets)")
        ax.set_ylabel(ylabel)
        ax.set_title(f"Exp 3(b): {ylabel.lower()} vs $W_s$ ($p_d$ = {PD_B}, $p_a$ = 0)")
        ax.legend()
        save(fig, fname)

    print(f"\n=== Exp 3(b): pd = {PD_B}, pa = 0 ===  (S&W: eta = {sw['efficiency']:.4f}, "
          f"attempts = {sw['attempts_per_packet']:.4f})")
    cols = ["GBN"] + [f"SR Wr={w}" for w in SR_WR]
    print(f"{'Ws':>4} " + " ".join(f"{c + ' eta':>12} {'att':>6}" for c in cols))
    for i, ws in enumerate(WS_B):
        print(f"{ws:>4} " + " ".join(f"{by[c][i]['efficiency']:12.4f} {by[c][i]['attempts_per_packet']:6.3f}"
                                     for c in cols))


if __name__ == "__main__":
    part_a()
    part_b()