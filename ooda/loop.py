"""Core OODA loop machinery.

The loop is intentionally generic: it knows nothing about *what* is being
observed or decided. You supply four callables — one per phase — and the loop
sequences them, threads a shared context between them, and repeats until a
decision asks it to stop (or an iteration cap is reached).
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar

logger = logging.getLogger("ooda")

# The context type is whatever the caller wants to thread through the loop.
C = TypeVar("C")


class Phase(enum.Enum):
    """The four phases of a single turn through the loop."""

    OBSERVE = "observe"
    ORIENT = "orient"
    DECIDE = "decide"
    ACT = "act"


class StopLoop(Exception):
    """Raise from any phase callback to halt the loop immediately.

    Unlike returning a stopping :class:`Decision`, this aborts the current turn
    without running the remaining phases.
    """


@dataclass
class Decision:
    """The output of the Decide phase.

    Attributes:
        action: An opaque value handed to the Act phase. ``None`` means "do
            nothing this turn".
        stop: When ``True``, the loop ends after this turn's Act phase runs.
        reason: Optional human-readable explanation, useful for logging/tracing.
    """

    action: Any = None
    stop: bool = False
    reason: str = ""


# Phase callback signatures. Each receives the shared context plus the output of
# the previous phase, and returns the input for the next phase.
ObserveFn = Callable[[C], Any]
OrientFn = Callable[[C, Any], Any]
DecideFn = Callable[[C, Any], Decision]
ActFn = Callable[[C, Any], None]


@dataclass
class OODALoop(Generic[C]):
    """A reusable Observe-Orient-Decide-Act control loop.

    Args:
        observe: ``observe(context) -> observation``.
        orient: ``orient(context, observation) -> orientation``.
        decide: ``decide(context, orientation) -> Decision``.
        act: ``act(context, action) -> None``. Only called when an action is
            present (i.e. ``decision.action is not None``).
        max_turns: Safety cap on iterations. ``None`` means run until a decision
            stops the loop. Defaults to 1000 to avoid accidental infinite loops.
    """

    observe: ObserveFn
    orient: OrientFn
    decide: DecideFn
    act: ActFn
    max_turns: Optional[int] = 1000

    # Number of completed turns across the loop's lifetime.
    turns: int = field(default=0, init=False)

    def step(self, context: C) -> Decision:
        """Run exactly one Observe-Orient-Decide-Act turn.

        Returns the :class:`Decision` produced by the Decide phase. The Act
        phase is invoked before returning when the decision carries an action.
        """
        observation = self.observe(context)
        logger.debug("observe -> %r", observation)

        orientation = self.orient(context, observation)
        logger.debug("orient -> %r", orientation)

        decision = self.decide(context, orientation)
        logger.debug("decide -> %r", decision)

        if decision.action is not None:
            self.act(context, decision.action)
            logger.debug("act <- %r", decision.action)

        self.turns += 1
        return decision

    def run(self, context: C) -> C:
        """Drive the loop until a decision stops it or ``max_turns`` is hit.

        Returns the (mutated) context so callers can inspect the final state.
        """
        self.turns = 0
        while self.max_turns is None or self.turns < self.max_turns:
            try:
                decision = self.step(context)
            except StopLoop as exc:
                logger.debug("loop halted by StopLoop: %s", exc)
                break
            if decision.stop:
                logger.debug("loop stopped by decision: %s", decision.reason)
                break
        else:
            logger.warning("loop reached max_turns=%s without stopping", self.max_turns)
        return context
