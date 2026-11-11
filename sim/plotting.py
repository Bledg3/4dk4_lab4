"""Shared plot style so every member's figures look the same.

Rules from the lab handout: label axes and units, mark simulation points with
markers, and do not join them with interpolated lines. Analytical curves may be
drawn as lines.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLOT_DIR = os.path.join(REPO, "plots")
RESULT_DIR = os.path.join(REPO, "results")

# Consistent look per protocol: (marker, colour)
STYLE = {
    "S&W": ("s", "#555555"),
    "GBN": ("o", "#1f77b4"),
    "SR1": ("^", "#d62728"),
    "SR2": ("v", "#2ca02c"),
    "SR3": ("D", "#9467bd"),
}

plt.rcParams.update({
    "figure.figsize": (7.5, 5),
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 11,
    "legend.fontsize": 9,
})


def save(fig, name):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path
