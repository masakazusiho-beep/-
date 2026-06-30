"""A small, dependency-free implementation of Boyd's OODA loop.

The OODA loop — Observe, Orient, Decide, Act — is a decision cycle popularized
by John Boyd. This package models it as a reusable control loop that you drive
with four pluggable callbacks operating over a shared, mutable context.
"""

from .loop import (
    Decision,
    OODALoop,
    Phase,
    StopLoop,
)

__all__ = [
    "Decision",
    "OODALoop",
    "Phase",
    "StopLoop",
]

__version__ = "0.1.0"
