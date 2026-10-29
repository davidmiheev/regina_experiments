#!/usr/bin/env python3
"""Figures for the E06 writeup, drawn from data/e06/summary.json.

Usage: figures.py [SUMMARY_JSON] [--out DIR]
"""

import argparse
import json
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V_TET = 1.0149416064096536

# Reference palette, light mode; slots 1-2 validate all-pairs (scatter-safe).
INK, INK_2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK_2, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": INK_2, "ytick.color": INK_2, "svg.fonttype": "path",
})


def volumes(summary, out):
    rng = random.Random(0)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for colour, census, label, dx in ((SERIES[0], "cusped-hyp-or", "orientable", -0.17),
                                      (SERIES[1], "cusped-hyp-nor", "non-orientable", 0.17)):
        pts = summary[census]["volume_points"]
        xs = [n + dx + rng.uniform(-0.12, 0.12) for n, _ in pts]
        ax.scatter(xs, [v for _, v in pts], s=3, color=colour, alpha=0.45, linewidths=0,
                   label=f"{label} ({len(pts):,} manifolds)", zorder=3, rasterized=False)
    ns = range(1, 8)
    ax.plot([n - 0.4 for n in ns] + [7.4], [V_TET * (n - 0.4) for n in ns] + [V_TET * 7.4],
            color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.annotate("volume = n · v$_{tet}$", (6.2, V_TET * 6.2), xytext=(-4, 6),
                textcoords="offset points", ha="right", color=INK_2, fontsize=8.5)
    ax.set_xticks(list(ns))
    ax.set_xlabel("n (tetrahedra in the census triangulation)")
    ax.set_ylabel("hyperbolic volume")
    ax.set_ylim(0, None)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=8.5, markerscale=3)
    for h in getattr(leg, "legend_handles", None) or leg.legendHandles:
        h.set_alpha(1)
    fig.tight_layout()
    fig.savefig(out / "volumes.svg")
    plt.close(fig)


def closed_trials(summary, out):
    t = summary["closed-hyp"]["trials"]
    k = t["k"]
    xs = list(range(k + 1))
    ys = [t["histogram"][str(i)] for i in xs]
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    ax.bar(xs, ys, width=0.8, color=SERIES[0], zorder=3)
    for x, y in zip(xs, ys):
        if y >= 40:
            ax.annotate(f"{y:,}", (x, y), xytext=(0, 3), textcoords="offset points",
                        ha="center", color=INK_2, fontsize=8)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_xlabel(f"constructions (of {k}) that gave the correct volume")
    ax.set_ylabel("closed triangulations")
    ax.grid(axis="x", visible=False)
    ax.margins(y=0.12)
    fig.tight_layout()
    fig.savefig(out / "closed_trials.svg")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", nargs="?", type=Path, default=ROOT / "data/e06/summary.json")
    ap.add_argument("--out", type=Path, default=HERE / "figures")
    args = ap.parse_args()
    summary = json.loads(args.summary.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    volumes(summary, args.out)
    closed_trials(summary, args.out)
    print(f"wrote {args.out}/volumes.svg, closed_trials.svg")


if __name__ == "__main__":
    main()
