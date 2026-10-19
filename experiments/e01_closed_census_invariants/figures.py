#!/usr/bin/env python3
"""Figures for the E01 writeup, drawn from an exported summary.json.

Usage: figures.py [SUMMARY_JSON] [--out DIR]
Defaults: data/e01/summary.json -> experiments/e01_closed_census_invariants/figures/
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Reference palette (light mode, validated: slots 1-2 pass CVD/normal-vision checks).
INK, INK_2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK_2, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": INK_2, "ytick.color": INK_2, "svg.fonttype": "path",
})


def separation(summary, out):
    cum = summary["cumulative"]
    rs = [int(r) for r in summary["levels"]]
    total = summary["manifolds"]
    h1 = summary["single"]["H1"]["separated"]
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    # The "all roots" curve is never below the "w = 1" curve, so put its end
    # label above and the other below to keep them apart.
    for colour, (key, label), dy in zip(SERIES, [("root1", "one root (w = 1)"),
                                                 ("both", "all roots w")], (-7, 7)):
        ys = [cum[key][str(r)]["separated"] for r in rs]
        ax.plot(rs, ys, color=colour, linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1, label=label, zorder=3)
        ax.annotate(f"{ys[-1]}", (rs[-1], ys[-1]), xytext=(8, dy),
                    textcoords="offset points", va="center", color=INK, fontsize=8.5)
    ax.axhline(h1, color=MUTED, linewidth=1, linestyle=(0, (4, 3)), zorder=2)
    ax.annotate(f"H₁ alone: {h1}", (rs[-1], h1), xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", color=INK_2, fontsize=8.5)
    ax.set_xticks(rs)
    ax.set_xlabel("R  (invariant = H₁ + TV₃ … TV_R)")
    ax.set_ylabel(f"manifolds identified uniquely\n(of {total})")
    ax.set_ylim(0, None)
    ax.set_xlim(rs[0] - 0.3, rs[-1] + 1.4)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "separation.svg")
    plt.close(fig)


def cost(summary, out):
    secs = summary["secs"]
    size = max(secs, key=int)
    rs = [int(r) for r in summary["levels"]]
    ys = [secs[size][f"tv{r}"] * 1000 for r in rs]
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    ax.plot(rs, ys, color=SERIES[0], linewidth=2, marker="o", markersize=5,
            markeredgecolor="white", markeredgewidth=1, zorder=3)
    for r, y in zip(rs, ys):
        ax.annotate(f"{y:.0f}" if y >= 10 else f"{y:.1f}", (r, y), xytext=(0, 7),
                    textcoords="offset points", ha="center", color=INK_2, fontsize=8)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xticks(rs)
    ax.set_xlabel("r")
    ax.set_ylabel(f"ms per manifold\n({size}-tetrahedron triangulations)")
    ax.margins(y=0.25)
    fig.tight_layout()
    fig.savefig(out / "cost.svg")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", nargs="?", type=Path, default=ROOT / "data/e01/summary.json")
    ap.add_argument("--out", type=Path, default=HERE / "figures")
    args = ap.parse_args()
    summary = json.loads(args.summary.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    separation(summary, args.out)
    cost(summary, args.out)
    print(f"wrote {args.out}/separation.svg, cost.svg")


if __name__ == "__main__":
    main()
