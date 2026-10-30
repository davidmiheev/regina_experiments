#!/usr/bin/env python3
"""Figures for the E03 writeup, drawn from data/e03/summary.json.

Usage: figures.py [SUMMARY_JSON] [--out DIR]
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

# Reference palette, light mode; slots 1-3 validate all-pairs.
INK, INK_2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK_2, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": INK_2, "ytick.color": INK_2, "svg.fonttype": "path",
})


def failure(summary, out):
    tab = summary["A"]["fail_by_k_mix"]
    ks = sorted(int(k) for k in tab)
    mixes = sorted(tab[str(ks[0])], key=int)
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    for colour, m in zip(SERIES, mixes):
        ys = [100 * tab[str(k)][m] for k in ks]
        label = "2-3 moves only" if m == "0" else f"2-3 moves + {m} random 4-4 move{'s' if m != '1' else ''} each"
        ax.plot(ks, ys, color=colour, linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1, label=label, zorder=3)
        ax.annotate(f"{ys[-1]:.1f}%", (ks[-1], ys[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", color=INK, fontsize=8.5)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ks)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlim(ks[0] / 1.3, ks[-1] * 1.6)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.set_xlabel("random moves applied to the minimal triangulation (k)")
    ax.set_ylabel("one simplify() call\nfails to get back")
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "failure_rate.svg")
    plt.close(fig)


def recognition(summary, out):
    by = summary["C"]["seconds_by_size"]
    sizes = sorted(int(s) for s in by)
    mean = [1000 * by[str(s)][1] for s in sizes]
    worst = [1000 * by[str(s)][2] for s in sizes]
    fig, ax = plt.subplots(figsize=(6.2, 2.9))
    for colour, ys, label, dy in ((SERIES[0], mean, "mean", -8), (SERIES[1], worst, "max", 8)):
        ax.plot(sizes, ys, color=colour, linewidth=2, marker="o", markersize=5,
                markeredgecolor="white", markeredgewidth=1, label=label, zorder=3)
        ax.annotate(f"{ys[-1]:.0f} ms", (sizes[-1], ys[-1]), xytext=(8, dy),
                    textcoords="offset points", va="center", color=INK, fontsize=8.5)
    ax.set_xlim(0, sizes[-1] * 1.15)
    ax.set_ylim(0, None)
    ax.set_xlabel("tetrahedra in the scrambled 3-sphere")
    ax.set_ylabel("3-sphere recognition\n(ms, incl. process start)")
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out / "sphere_recognition.svg")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", nargs="?", type=Path, default=ROOT / "data/e03/summary.json")
    ap.add_argument("--out", type=Path, default=HERE / "figures")
    args = ap.parse_args()
    summary = json.loads(args.summary.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    failure(summary, args.out)
    recognition(summary, args.out)
    print(f"wrote {args.out}/failure_rate.svg, sphere_recognition.svg")


if __name__ == "__main__":
    main()
