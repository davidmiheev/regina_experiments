"""Iterate over the census data files that ship with the regina-normal package."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import regina

EXAMPLES_DIR = Path(os.environ.get("REGINA_EXAMPLES_DIR", "/usr/share/regina-normal/examples"))

# Short name -> (file, packet type, description)
CENSUSES = {
    "closed-or": ("closed-or-census.rga", regina.PacketOfTriangulation3,
                  "Closed orientable prime minimal triangulations, <= 10 tetrahedra (Burton)"),
    "closed-nor": ("closed-nor-census.rga", regina.PacketOfTriangulation3,
                   "Closed non-orientable P2-irreducible minimal triangulations"),
    "closed-hyp": ("closed-hyp-census.rga", regina.PacketOfTriangulation3,
                   "Hodgson-Weeks closed hyperbolic census, incl. 18 non-orientable "
                   "(label = '<volume> : <cusped>(p, q)')"),
    "cusped-hyp-or": ("cusped-hyp-or-census.rga", regina.PacketOfTriangulation3,
                      "Cusped hyperbolic orientable census, <= 7 tetrahedra"),
    "cusped-hyp-nor": ("cusped-hyp-nor-census.rga", regina.PacketOfTriangulation3,
                       "Cusped hyperbolic non-orientable census, <= 7 tetrahedra"),
    "knots": ("knot-census.rga", regina.PacketOfLink,
              "Prime knots and links (Hoste-Thistlethwaite / Christy tables)"),
    "virtual": ("virtual-census.rga", regina.PacketOfLink,
                "Virtual knots (Green's table)"),
}


def iter_census(name: str, max_size: int | None = None,
                min_size: int = 0, limit: int | None = None) -> Iterator[tuple[str, object]]:
    """Yield ``(label, object)`` for every triangulation/link in a census.

    ``size`` means tetrahedra for triangulations and crossings for links.
    Objects are the packets themselves, which behave as Triangulation3 / Link.
    """
    try:
        filename, ptype, _ = CENSUSES[name]
    except KeyError:
        raise ValueError(f"unknown census {name!r}; choose from {sorted(CENSUSES)}") from None
    root = regina.open(str(EXAMPLES_DIR / filename))
    if root is None:
        raise FileNotFoundError(EXAMPLES_DIR / filename)
    count = 0
    for pkt in root.descendants():
        if not isinstance(pkt, ptype):
            continue
        n = pkt.size()
        if n < min_size or (max_size is not None and n > max_size):
            continue
        yield pkt.label(), pkt
        count += 1
        if limit is not None and count >= limit:
            return
