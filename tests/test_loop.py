"""Tests for the OODA loop core."""

from __future__ import annotations

import pytest

from ooda import Decision, OODALoop, Phase, StopLoop


def test_phase_values():
    assert [p.value for p in Phase] == ["observe", "orient", "decide", "act"]


def test_single_step_runs_all_phases_in_order():
    calls = []

    def observe(ctx):
        calls.append("observe")
        return 1

    def orient(ctx, obs):
        calls.append("orient")
        return obs + 1

    def decide(ctx, orientation):
        calls.append("decide")
        return Decision(action=orientation, stop=True)

    def act(ctx, action):
        calls.append(f"act:{action}")

    loop = OODALoop(observe, orient, decide, act)
    decision = loop.step({})

    assert calls == ["observe", "orient", "decide", "act:2"]
    assert decision.stop is True
    assert loop.turns == 1


def test_act_skipped_when_action_is_none():
    acted = []
    loop = OODALoop(
        observe=lambda ctx: None,
        orient=lambda ctx, obs: None,
        decide=lambda ctx, o: Decision(action=None, stop=True),
        act=lambda ctx, a: acted.append(a),
    )
    loop.step({})
    assert acted == []


def test_run_stops_on_decision():
    ctx = {"n": 0}

    def decide(ctx, orientation):
        return Decision(action="inc", stop=ctx["n"] >= 3)

    def act(ctx, action):
        ctx["n"] += 1

    loop = OODALoop(
        observe=lambda ctx: ctx["n"],
        orient=lambda ctx, obs: obs,
        decide=decide,
        act=act,
    )
    result = loop.run(ctx)
    # The stopping turn still runs Act, so the fourth increment lands too.
    assert result["n"] == 4
    assert loop.turns == 4


def test_run_respects_max_turns():
    loop = OODALoop(
        observe=lambda ctx: None,
        orient=lambda ctx, obs: None,
        decide=lambda ctx, o: Decision(action=None, stop=False),
        act=lambda ctx, a: None,
        max_turns=5,
    )
    loop.run({})
    assert loop.turns == 5


def test_stoploop_halts_immediately():
    acted = []

    def orient(ctx, obs):
        raise StopLoop("abort")

    loop = OODALoop(
        observe=lambda ctx: None,
        orient=orient,
        decide=lambda ctx, o: Decision(action="x"),
        act=lambda ctx, a: acted.append(a),
    )
    loop.run({})
    assert acted == []
    assert loop.turns == 0


def test_thermostat_example_settles():
    from examples.thermostat import Room, act, decide, observe, orient

    room = Room(temperature=15.0)
    loop = OODALoop(observe, orient, decide, act, max_turns=50)
    loop.run(room)
    assert abs(room.temperature - room.target) <= room.tolerance


def test_decision_defaults():
    d = Decision()
    assert d.action is None
    assert d.stop is False
    assert d.reason == ""
