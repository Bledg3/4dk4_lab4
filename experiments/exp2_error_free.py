"""Experiment 2: continuously backlogged source, no errors (pd = pa = 0).

Sweeps Ws for GBN (Wr = 1) and SR (three Wr values), with S&W as a reference,
and compares against the analytical efficiency min(1, Ws * T_tx / (T_tx + 2 T_prop)).

With no errors the simulation is deterministic, so one seed is enough.

Run from the repo root:  py -3.12 experiments/exp2_error_free.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from sim import config, theory  # noqa: E402
from sim.arq import simulate  # noqa: E402
from sim.plotting import RESULT_DIR, STYLE, plt, save  # noqa: E402

WS_VALUES = list(range(1, 21)) + [22, 25, 30, 35, 40]
SR_WR = [2, 6, 11]
SIM_TIME = config.SIM_TIME
WARMUP = config.WARMUP


def main():
    rows = []
    sw = simulate(1, 1, sim_time=SIM_TIME, warmup=WARMUP)["efficiency"]
    rows.append(("S&W", 1, 1, sw, theory.efficiency_error_free(1)))

    curves = {"GBN": []}
    for wr in SR_WR:
        curves[f"SR Wr={wr}"] = []
    for Ws in WS_VALUES:
        th = theory.efficiency_error_free(Ws)
        e = simulate(Ws, 1, sim_time=SIM_TIME, warmup=WARMUP)["efficiency"]
        curves["GBN"].append(e)
        rows.append(("GBN", Ws, 1, e, th))
        for wr in SR_WR:
            e = simulate(Ws, wr, sim_time=SIM_TIME, warmup=WARMUP)["efficiency"]
            curves[f"SR Wr={wr}"].append(e)
            rows.append(("SR", Ws, wr, e, th))

    os.makedirs(RESULT_DIR, exist_ok=True)
    csv_path = os.path.join(RESULT_DIR, "exp2_efficiency.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protocol", "Ws", "Wr", "efficiency_sim", "efficiency_theory", "abs_error"])
        for p, ws, wr, e, th in rows:
            w.writerow([p, ws, wr, f"{e:.6f}", f"{th:.6f}", f"{abs(e - th):.2e}"])

    # ---------------- plot ----------------
    fig, ax = plt.subplots()
    ws_fine = np.linspace(1, max(WS_VALUES), 400)
    ax.plot(ws_fine, [theory.efficiency_error_free(w) for w in ws_fine], "k--", lw=1,
            label=r"Analysis: $\min(1,\ W_s/11)$", zorder=1)
    ax.axhline(sw, color=STYLE["S&W"][1], ls=":", lw=1.5,
               label=f"S&W simulated ($W_s=W_r=1$), $\\eta$ = {sw:.4f}", zorder=1)
    ax.axvline(config.W_FULL, color="grey", lw=0.8, alpha=0.6)
    ax.text(config.W_FULL + 0.4, 0.45, f"$W_s$ = {config.W_FULL}\n(full utilization)",
            fontsize=9, color="grey")

    # Curves overlap exactly with no errors, so use decreasing marker sizes
    # and hollow markers to keep each one visible.
    series = [("GBN ($W_r$=1)", curves["GBN"], STYLE["GBN"], 11)]
    for i, wr in enumerate(SR_WR):
        series.append((f"SR ($W_r$={wr})", curves[f"SR Wr={wr}"], STYLE[f"SR{i + 1}"], 8.5 - 2 * i))
    for label, ys, (marker, colour), size in series:
        ax.plot(WS_VALUES, ys, ls="none", marker=marker, ms=size, mfc="none",
                mec=colour, mew=1.4, label=label + " simulated", zorder=3)

    ax.set_xlabel("Send window size $W_s$ (packets)")
    ax.set_ylabel(r"Link efficiency $\eta$")
    ax.set_title("Exp. 2: efficiency vs send window, no errors ($p_d=p_a=0$)\n"
                 r"$T_{tx}$ = 1 ms, RTT = 10 ms, $T_{out}$ = 15 ms, "
                 f"run = {SIM_TIME / 1000:.0f} s", fontsize=11)
    ax.set_xlim(0, max(WS_VALUES) + 1)
    ax.set_ylim(0, 1.08)
    ax.legend(loc="lower right")
    path = save(fig, "exp2_efficiency_vs_ws.png")

    worst = max(abs(e - th) for _, _, _, e, th in rows)
    print(f"S&W efficiency: sim = {sw:.5f}, theory = {theory.efficiency_error_free(1):.5f}")
    print(f"{'Ws':>4} {'theory':>8} {'GBN':>8} " + " ".join(f"{'SR Wr=' + str(w):>9}" for w in SR_WR))
    for i, Ws in enumerate(WS_VALUES):
        print(f"{Ws:>4} {theory.efficiency_error_free(Ws):8.4f} {curves['GBN'][i]:8.4f} "
              + " ".join(f"{curves[f'SR Wr={w}'][i]:9.4f}" for w in SR_WR))
    print(f"\nMax |sim - theory| over all points: {worst:.2e}")
    print(f"CSV:  {csv_path}\nPlot: {path}")


if __name__ == "__main__":
    main()
