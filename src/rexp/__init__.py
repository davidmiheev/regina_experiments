"""Shared helpers for Regina experiments.

Import as ``import rexp``; requires the ``regina`` Python module
(see ``scripts/install-regina-ubuntu.sh``).
"""

import regina

from .census import CENSUSES, iter_census
from .runlog import Run, timed

__all__ = ["regina", "CENSUSES", "iter_census", "Run", "timed", "regina_version"]


def regina_version() -> str:
    return regina.versionString()
