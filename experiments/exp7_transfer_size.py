"""Experiment 7: effect of transfer size N.

Repeats Experiment 6 (same plot format) for N = 10 and N = 1000, for the
error-free case and pd = pa = 0.05.

Run from the repo root:  py -3.12 experiments/exp7_transfer_size.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.exp6_finite_transfer import case_tag, run_and_plot  # noqa: E402
from sim.plotting import RESULT_DIR  # noqa: E402

N_VALUES = [10, 1000]
CASES = [(0.0, 0.0), (0.05, 0.05)]     # (pd, pa)
REPS = {10: 400, 1000: 60}             # fewer runs for large N (each run is longer)


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(os.path.join(RESULT_DIR, "exp7_transfer_size.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["N", "pd", "pa", "protocol", "Ws", "Wr", "completion_mean_ms"])
        for pd, pa in CASES:
            for n in N_VALUES:
                run_and_plot(pd, pa, n, REPS[n], "Exp. 7",
                             f"exp7_completion_vs_ws_N{n}_{case_tag(pd, pa)}.png", w)


if __name__ == "__main__":
    main()
