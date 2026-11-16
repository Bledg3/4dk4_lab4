"""Experiment 5: effect of the retransmission timeout (continuously backlogged source).

Sweeps T_out for S&W, GBN and SR (three Wr values) with fixed pd, pa and Ws,
and plots efficiency and attempts per delivered packet vs T_out.

Run from the repo root:  py -3.12 experiments/exp5_timeout.py
"""

import csv
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter  # noqa: E402

from sim import config  # noqa: E402
from sim.arq import simulate  # noqa: E402
from sim.plotting import RESULT_DIR, STYLE, plt, save  # noqa: E402

PD, PA = 0.1, 0.1
WS = 16
SR_WR = [2, 6, 11]
T_OUT_VALUES = [2, 4, 6, 8, 9, 10, 11, 12, 13, 15, 18, 20, 25, 30, 40, 50, 60]

# (style key, legend label, Ws, Wr)
PROTOCOLS = [("S&W", "S&W ($W_s=W_r=1$)", 1, 1),
             ("GBN", f"GBN ($W_s$={WS}, $W_r$=1)", WS, 1)]
PROTOCOLS += [(f"SR{i + 1}", f"SR ($W_s$={WS}, $W_r$={wr})", WS, wr) for i, wr in enumerate(SR_WR)]


def main():
    # Mean efficiency and attempts over the shared seeds for every (protocol, T_out)
    eff, att = {}, {}
    for key, _, ws, wr in PROTOCOLS:
        eff[key], att[key] = [], []
        for t_out in T_OUT_VALUES:
            runs = [simulate(ws, wr, pd=PD, pa=PA, t_out=t_out, seed=s) for s in config.SEEDS]
            eff[key].append(statistics.mean(r["efficiency"] for r in runs))
            att[key].append(statistics.mean(r["attempts_per_packet"] for r in runs))

    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(os.path.join(RESULT_DIR, "exp5_timeout.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protocol", "Ws", "Wr", "t_out_ms", "efficiency", "attempts_per_packet"])
        for key, _, ws, wr in PROTOCOLS:
            for i, t_out in enumerate(T_OUT_VALUES):
                w.writerow([key, ws, wr, t_out, f"{eff[key][i]:.6f}", f"{att[key][i]:.6f}"])

    subtitle = f"$p_d$ = {PD}, $p_a$ = {PA}, $W_s$ = {WS}, $T_{{tx}}$ = 1 ms, RTT = 10 ms"
    for data, ylabel, title, fname in [
            (eff, r"Link efficiency $\eta$", "Exp. 5: efficiency vs retransmission timeout",
             "exp5_efficiency_vs_tout.png"),
            (att, "Transmission attempts per delivered packet",
             "Exp. 5: attempts per delivered packet vs retransmission timeout",
             "exp5_attempts_vs_tout.png")]:
        fig, ax = plt.subplots()
        for key, label, _, _ in PROTOCOLS:
            marker, colour = STYLE[key]
            ax.plot(T_OUT_VALUES, data[key], ls="none", marker=marker,
                    color=colour, mfc="none", mew=1.3, label=label)
        if data is eff:
            ax.set_ylim(0, None)
        else:
            ax.set_yscale("log")
            ax.yaxis.set_major_locator(LogLocator(subs=(1, 1.5, 2, 3, 4, 5)))
            ax.yaxis.set_major_formatter(ScalarFormatter())
            ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel(r"Retransmission timeout $T_{out}$ (ms)")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{title}\n{subtitle}", fontsize=11)
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
        print(save(fig, fname))


if __name__ == "__main__":
    main()
