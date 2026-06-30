"""A toy thermostat driven by the OODA loop.

Observe the current temperature, orient by comparing it to a target band,
decide whether to heat/cool/idle, and act by nudging the temperature. The loop
stops once the temperature settles inside the comfort band.

Run with:  python -m examples.thermostat
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ooda import Decision, OODALoop


@dataclass
class Room:
    temperature: float
    target: float = 21.0
    tolerance: float = 0.5
    history: List[float] = field(default_factory=list)


def observe(room: Room) -> float:
    return room.temperature


def orient(room: Room, temp: float) -> float:
    # Signed distance from the target; positive means too hot.
    return temp - room.target


def decide(room: Room, delta: float) -> Decision:
    if abs(delta) <= room.tolerance:
        return Decision(action=None, stop=True, reason="within comfort band")
    if delta > 0:
        return Decision(action="cool", reason=f"too hot by {delta:.1f}")
    return Decision(action="heat", reason=f"too cold by {-delta:.1f}")


def act(room: Room, action: str) -> None:
    room.temperature += 1.0 if action == "heat" else -1.0
    room.history.append(room.temperature)


def main() -> None:
    room = Room(temperature=15.0)
    loop: OODALoop[Room] = OODALoop(observe, orient, decide, act, max_turns=50)
    loop.run(room)
    print(f"Settled at {room.temperature:.1f}°C after {loop.turns} turns")
    print("Trajectory:", " -> ".join(f"{t:.0f}" for t in room.history))


if __name__ == "__main__":
    main()
