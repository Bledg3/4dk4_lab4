"""Experiment 1: simulation verification.

Part A - short event traces for S&W, GBN and SR with (pd, pa) = (0, 0) and
         (0.5, 0.5), to be checked by hand.
Part B - automated checks over long runs and all seeds:
         1. every packet is delivered exactly once and in order (finite runs);
         2. measured data/ACK loss rates match pd and pa;
         3. error-free efficiency matches min(1, Ws/11);
         4. error-free finite completion time matches the closed form;
         5. S&W efficiency with errors matches the renewal formula.

Run from the repo root:  py -3.12 experiments/exp1_verification.py
"""

import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim import config, theory  # noqa: E402
from sim.arq import simulate  # noqa: E402
from sim.plotting import RESULT_DIR  # noqa: E402

TRACE_CASES = [
    # (label, Ws, Wr, N)
    ("Stop-and-Wait (Ws=1, Wr=1)", 1, 1, 3),
    ("Go-Back-N (Ws=4, Wr=1)", 4, 1, 6),
    ("Selective Repeat (Ws=4, Wr=4)", 4, 4, 6),
]
ERROR_CASES = [(0.0, 0.0), (0.5, 0.5)]
TRACE_SEED = config.SEEDS[0]
MAX_TRACE_LINES = 150

HEADER = ("  time(ms)  event" + " " * 41 + "state after event\n"
          "  " + "-" * 120)


def part_a():
    out = []
    out.append("EXPERIMENT 1 - EVENT TRACES")
    out.append(f"Parameters: T_tx = {config.T_TX} ms, one-way delay = {config.T_PROP} ms, "
               f"timeout = {config.T_OUT} ms (timer starts at end of transmission), "
               f"seed = {TRACE_SEED}")
    out.append("ACK(cum=c, sel=s): cumulative ACK of all seq < c, plus selective ACK of seq s "
               "(None if the packet was not accepted).")
    out.append("S[...] = sender state, R[...] = receiver state.\n")
    for pd, pa in ERROR_CASES:
        for label, Ws, Wr, N in TRACE_CASES:
            r = simulate(Ws, Wr, pd=pd, pa=pa, num_packets=N, seed=TRACE_SEED,
                         trace=True, max_trace_lines=MAX_TRACE_LINES)
            out.append("=" * 122)
            out.append(f"{label}   pd = {pd}, pa = {pa}, N = {N} packets")
            out.append("=" * 122)
            out.append(HEADER)
            out.extend(r["trace"])
            if len(r["trace"]) >= MAX_TRACE_LINES:
                out.append(f"  ... trace truncated at {MAX_TRACE_LINES} lines ...")
            out.append(f"  Result: delivered order = {r['delivered_seqs']}, "
                       f"transmissions = {r['transmissions']}, "
                       f"completion time = {r['completion_time']:.3f} ms\n")
    return "\n".join(out)


def check(name, ok, detail, results):
    results.append((name, ok, detail))


def part_b():
    res = []
    protocols = [("S&W", 1, 1), ("GBN", 8, 1), ("GBN", 15, 1),
                 ("SR", 8, 4), ("SR", 15, 8), ("SR", 15, 15)]

    # 1 & 2: integrity and loss rates over many seeds and error settings
    for pd, pa in [(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.5, 0.5)]:
        for name, Ws, Wr in protocols:
            N = 2000 if pd < 0.5 else 500
            ok_all = True
            dl, al = [], []
            for seed in config.SEEDS:
                r = simulate(Ws, Wr, pd=pd, pa=pa, num_packets=N, seed=seed)
                ok_all &= r["delivered_seqs"] == list(range(N))
                ok_all &= r["completion_time"] is not None
                dl.append(r["data_loss_rate"])
                al.append(r["ack_loss_rate"])
            check(f"in-order exactly-once delivery {name} Ws={Ws} Wr={Wr} pd={pd} pa={pa}",
                  ok_all, f"N={N}, {len(config.SEEDS)} seeds", res)
            if pd > 0 or pa > 0:
                mdl, mal = statistics.mean(dl), statistics.mean(al)
                ok = abs(mdl - pd) < 0.02 and abs(mal - pa) < 0.02
                check(f"loss rates {name} Ws={Ws} Wr={Wr} pd={pd} pa={pa}", ok,
                      f"measured data loss = {mdl:.4f}, ACK loss = {mal:.4f}", res)

    # 3: error-free efficiency
    worst = 0.0
    for Ws in list(range(1, 21)) + [30]:
        for Wr in [1, 2, 6, 11]:
            e = simulate(Ws, Wr, sim_time=20_000)["efficiency"]
            worst = max(worst, abs(e - theory.efficiency_error_free(Ws)))
    check("error-free efficiency = min(1, Ws/11)", worst < 1e-3,
          f"max |sim - theory| = {worst:.2e}", res)

    # 4: error-free completion time
    worst = 0.0
    for N in [1, 7, 50, 100]:
        for Ws in [1, 2, 5, 10, 11, 12, 30]:
            for Wr in [1, 3, Ws]:
                r = simulate(Ws, Wr, num_packets=N)
                worst = max(worst, abs(r["completion_time"]
                                       - theory.completion_time_error_free(N, Ws)))
    check("error-free completion time = closed form", worst < 1e-9,
          f"max |sim - theory| = {worst:.2e} ms", res)

    # 5: S&W with errors vs renewal formula
    for pd, pa in [(0.1, 0.0), (0.2, 0.1), (0.5, 0.5)]:
        effs = [simulate(1, 1, pd=pd, pa=pa, sim_time=500_000, seed=s)["efficiency"]
                for s in config.SEEDS]
        m = statistics.mean(effs)
        th = theory.efficiency_sw(pd, pa)
        check(f"S&W efficiency pd={pd} pa={pa}", abs(m - th) / th < 0.02,
              f"sim = {m:.5f} (seeds: {min(effs):.5f}..{max(effs):.5f}), "
              f"theory = {th:.5f}, rel. error = {abs(m - th) / th * 100:.2f}%", res)

    lines = ["EXPERIMENT 1 - AUTOMATED CHECKS", f"Seeds: {config.SEEDS}", ""]
    for name, ok, detail in res:
        lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    n_fail = sum(not ok for _, ok, _ in res)
    lines.append("")
    lines.append(f"{len(res) - n_fail}/{len(res)} checks passed")
    return "\n".join(lines), n_fail


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    traces = part_a()
    with open(os.path.join(RESULT_DIR, "exp1_traces.txt"), "w") as f:
        f.write(traces + "\n")
    checks, n_fail = part_b()
    with open(os.path.join(RESULT_DIR, "exp1_checks.txt"), "w") as f:
        f.write(checks + "\n")
    print(checks)
    print(f"\nTraces written to {os.path.join(RESULT_DIR, 'exp1_traces.txt')}")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
