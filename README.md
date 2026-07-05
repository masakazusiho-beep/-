# ooda

A small, dependency-free Python implementation of Boyd's **OODA loop** —
**O**bserve, **O**rient, **D**ecide, **A**ct.

The OODA loop is a decision cycle popularized by military strategist John Boyd.
This package models it as a reusable control loop: you supply four callbacks
(one per phase), and the loop sequences them, threads a shared context between
them, and repeats until a decision asks it to stop.

## Install

No dependencies for the library itself. Clone the repo and use it directly, or
install in editable mode:

```bash
pip install -e .
```

Running the tests requires `pytest`:

```bash
pip install pytest
```

## Usage

```python
from ooda import Decision, OODALoop

ctx = {"n": 0}

loop = OODALoop(
    observe=lambda c: c["n"],                        # gather raw input
    orient=lambda c, obs: obs,                        # interpret it
    decide=lambda c, o: Decision(action="inc",        # choose an action
                                 stop=o >= 3),
    act=lambda c, action: c.__setitem__("n", c["n"] + 1),  # carry it out
)

loop.run(ctx)
print(ctx["n"], "completed in", loop.turns, "turns")
```

### Phases

| Phase    | Signature                                     | Purpose                                  |
|----------|-----------------------------------------------|------------------------------------------|
| Observe  | `observe(context) -> observation`             | Gather raw data from the environment     |
| Orient   | `orient(context, observation) -> orientation` | Interpret the data into a useful form    |
| Decide   | `decide(context, orientation) -> Decision`    | Choose an action and whether to stop     |
| Act      | `act(context, action) -> None`                | Carry out the action (skipped if `None`) |

A `Decision` carries an `action` (handed to Act; `None` skips it), a `stop`
flag, and an optional `reason` for logging/tracing.

### Stopping

The loop ends when:

- a `Decision` sets `stop=True` (the Act phase still runs that turn), or
- any callback raises `StopLoop` (halts immediately, skipping remaining phases), or
- `max_turns` is reached (defaults to `1000` as an infinite-loop guard; set
  `None` to disable).

Call `loop.step(context)` to run a single turn, or `loop.run(context)` to drive
the loop to completion. Both mutate and return the context.

## Example

A toy thermostat that heats/cools a room until it settles in a comfort band:

```bash
python -m examples.thermostat
```

## Tests

```bash
python -m pytest
```

## Also in this repo

- [`note_auto/`](note_auto/README.md) — a pipeline that automates note.com articles
  end to end (idea research → article generation with Claude → draft posting via
  Playwright → scheduled runs).
- [`bakers-note/`](bakers-note/README.md) — ベーカーズ％ノート: 製菓レシピをベーカーズ％に
  変換・スケールする PWA（ホーム画面に追加可能、GitHub Pages で公開）。
