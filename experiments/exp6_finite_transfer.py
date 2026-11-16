"""Experiment 6: finite transfer of N = 100 packets.

For each error case, plots the mean transfer completion time vs Ws for GBN
and SR (three Wr values), with S&W as a reference. With errors, each point is
the mean of REPS independent runs; error-free runs are deterministic, so one
run is enough.

Run from the repo root:  py -3.12 experiments/exp6_finite_transfer.py
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

N = 100
CASES = [(0.0, 0.0), (0.05, 0.0), (0.05, 0.05)]     # (pd, pa)
WS_VALUES = list(range(1, 21)) + [22, 25, 30, 35, 40]
SR_WR = [2, 6, 11]
REPS = 200

# (style key, legend label, Wr); S&W is plotted separately as a reference line
PROTOCOLS = [("GBN", "GBN ($W_r$=1)", 1)]
PROTOCOLS += [(f"SR{i + 1}", f"SR ($W_r$={wr})", wr) for i, wr in enumerate(SR_WR)]
MARKER_SIZE = {"GBN": 9, "SR1": 7.5, "SR2": 6, "SR3": 4.5}   # overlapping points stay visible


def mean_completion(ws, wr, pd, pa, n, reps):
    """Mean completion time over reps runs"""
    if pd == 0 and pa == 0:
        seeds = config.SEEDS[:1]
    else:
        seeds = (list(config.SEEDS) + [1_000 + i for i in range(reps)])[:reps]
    return statistics.mean(simulate(ws, wr, pd=pd, pa=pa, num_packets=n, seed=s)["completion_time"]
                           for s in seeds)


def run_and_plot(pd, pa, n, reps, title_prefix, fname, writer):
    """Run every protocol and Ws for one case, write CSV rows and save the plot."""
    sw = mean_completion(1, 1, pd, pa, n, reps)
    writer.writerow([n, pd, pa, "S&W", 1, 1, f"{sw:.3f}"])
    means = {}
    for key, _, wr in PROTOCOLS:
        means[key] = [mean_completion(ws, wr, pd, pa, n, reps) for ws in WS_VALUES]
        for ws, m in zip(WS_VALUES, means[key]):
            writer.writerow([n, pd, pa, key, ws, wr, f"{m:.3f}"])

    fig, ax = plt.subplots()
    ax.axhline(sw, color=STYLE["S&W"][1], ls=":", lw=1.5, label=f"S&W = {sw:.1f} ms")
    for key, label, _ in PROTOCOLS:
        marker, colour = STYLE[key]
        ax.plot(WS_VALUES, means[key], ls="none", marker=marker, ms=MARKER_SIZE[key],
                color=colour, mfc="none", mew=1.3, label=label)
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(subs=(1, 1.5, 2, 3, 5)))
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Send window size $W_s$ (packets)")
    ax.set_ylabel("Mean transfer completion time (ms)")
    ax.set_title(f"{title_prefix}: completion time vs $W_s$, N = {n}\n"
                 f"$p_d$ = {pd}, $p_a$ = {pa}, $T_{{out}}$ = {config.T_OUT:g} ms", fontsize=11)
    ax.legend(loc="upper right")
    print(save(fig, fname))


def case_tag(pd, pa):
    return f"pd{pd:g}_pa{pa:g}".replace(".", "p")


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(os.path.join(RESULT_DIR, "exp6_finite_transfer.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["N", "pd", "pa", "protocol", "Ws", "Wr", "completion_mean_ms"])
        for pd, pa in CASES:
            run_and_plot(pd, pa, N, REPS, "Exp. 6",
                         f"exp6_completion_vs_ws_{case_tag(pd, pa)}.png", w)


if __name__ == "__main__":
    main()
