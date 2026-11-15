"""Run many (Ws, Wr, pd, pa, seed) points in parallel and average over seeds."""

import math
import os
from concurrent.futures import ProcessPoolExecutor

from sim import config
from sim.arq import simulate

# Two-sided Student t, 95 %, for n - 1 degrees of freedom (n = number of seeds)
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262}


def _run(kw):
    r = simulate(**kw)
    return {k: r[k] for k in ("Ws", "Wr", "pd", "pa", "t_out", "seed",
                              "efficiency", "attempts_per_packet",
                              "data_loss_rate", "ack_loss_rate")}


def run_points(points, seeds=config.SEEDS, workers=None, **common):
    """points: list of dicts of simulate() kwargs (without seed).

    Returns one dict per point with mean and 95 % CI half-width of
    efficiency and attempts per packet across seeds, plus the raw runs.
    """
    jobs = [dict(common, **p, seed=s) for p in points for s in seeds]
    with ProcessPoolExecutor(max_workers=workers or os.cpu_count()) as ex:
        raw = list(ex.map(_run, jobs, chunksize=4))
    out = []
    n = len(seeds)
    for i, p in enumerate(points):
        runs = raw[i * n:(i + 1) * n]
        row = dict(p)
        for key in ("efficiency", "attempts_per_packet"):
            vals = [r[key] for r in runs]
            m = sum(vals) / n
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
            row[key] = m
            row[key + "_ci"] = _T95.get(n - 1, 1.96) * sd / math.sqrt(n)
        row["runs"] = runs
        out.append(row)
    return out


def write_csv(rows, path):
    import csv
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["protocol", "Ws", "Wr", "pd", "pa", "seed",
                    "efficiency", "attempts_per_packet",
                    "measured_data_loss", "measured_ack_loss"])
        for row in rows:
            for r in row["runs"]:
                w.writerow([row.get("label", ""), r["Ws"], r["Wr"], r["pd"], r["pa"], r["seed"],
                            f"{r['efficiency']:.6f}", f"{r['attempts_per_packet']:.6f}",
                            f"{r['data_loss_rate']:.5f}", f"{r['ack_loss_rate']:.5f}"])
