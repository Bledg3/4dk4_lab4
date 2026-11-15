"""Experiment 4: continuously backlogged source, data-packet AND ACK errors.

pd fixed at 0.1, pa swept from 0 to 0.9.
Same windows as Exp 3(a): GBN Ws = 64, SR Ws = 64 with Wr = 11, 32, 64.
A small window (GBN Ws = 4, SR Ws = Wr = 4) is added to show the effect of
window size on ACK errors. S&W is included as a reference.

Plots: (i) efficiency vs pa, (ii) transmission attempts per delivered packet vs pa.
Every point is averaged over the 5 shared seeds; error bars are 95 % CIs.

Run from the repo root:  py -3.12 experiments/exp4_ack_errors.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim import config  # noqa: E402
from sim.batch import run_points, write_csv  # noqa: E402
from sim.plotting import RESULT_DIR, plt, save  # noqa: E402

PD = 0.1
PA_VALUES = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# (label, Ws, Wr, marker)
PROTOCOLS = [
    ("S&W", 1, 1, "s"),
    ("GBN Ws=4", 4, 1, "o"),
    ("GBN Ws=64", 64, 1, "o"),
    ("SR Ws=Wr=4", 4, 4, "^"),
    ("SR Ws=64, Wr=11", 64, 11, "v"),
    ("SR Ws=64, Wr=32", 64, 32, "D"),
    ("SR Ws=64, Wr=64", 64, 64, "^"),
]

COMMON = dict(sim_time=config.SIM_TIME, warmup=config.WARMUP)


def main():
    pts, labels = [], []
    for pa in PA_VALUES:
        for lab, ws, wr, _ in PROTOCOLS:
            pts.append(dict(Ws=ws, Wr=wr, pd=PD, pa=pa)); labels.append(lab)
    rows = run_points(pts, **COMMON)
    for r, lab in zip(rows, labels):
        r["label"] = lab
    write_csv(rows, os.path.join(RESULT_DIR, "exp4_vs_pa.csv"))
    by = {lab: [r for r in rows if r["label"] == lab] for lab, _, _, _ in PROTOCOLS}

    for key, ylabel, fname in [
        ("efficiency", "Link efficiency", "exp4_efficiency_vs_pa.png"),
        ("attempts_per_packet", "Transmission attempts per delivered packet",
         "exp4_attempts_vs_pa.png"),
    ]:
        fig, ax = plt.subplots()
        for lab, _, _, marker in PROTOCOLS:
            ax.errorbar(PA_VALUES, [r[key] for r in by[lab]],
                        yerr=[r[key + "_ci"] for r in by[lab]],
                        ls="none", marker=marker, capsize=3, label=lab)
        if key == "attempts_per_packet":
            ax.set_yscale("log")   # S&W reaches ~11, the others stay near 1 to 4
        ax.set_xlabel("ACK error probability $p_a$")
        ax.set_ylabel(ylabel)
        ax.set_title(f"Exp 4: {ylabel.lower()} vs $p_a$ ($p_d$ = {PD})")
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        save(fig, fname)

    print(f"\n=== Exp 4: pd = {PD} ===  (eta / attempts per packet)")
    print(f"{'pa':>5} " + " ".join(f"{lab:>17}" for lab, _, _, _ in PROTOCOLS))
    for i, pa in enumerate(PA_VALUES):
        print(f"{pa:5.2f} " + " ".join(
            f"{by[lab][i]['efficiency']:8.4f} / {by[lab][i]['attempts_per_packet']:6.3f}"
            for lab, _, _, _ in PROTOCOLS))


if __name__ == "__main__":
    main()
