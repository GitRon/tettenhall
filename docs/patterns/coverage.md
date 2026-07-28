# Coverage

The gate is **100% branch coverage**, configured as `branch = true` and `fail_under = 100` in
`pyproject.toml`. Run it with `pytest --cov`.

Statement coverage alone is not enough: it counts an `if` as covered once the body has run, so a missing
`else` and an unexercised loop exit both pass unnoticed. Branch coverage is what makes "one test per
branch" verifiable instead of aspirational.

**The suite meets the gate. Keep it there.**

- Don't lower `fail_under` to turn a red run green.
- Don't reach for `# pragma: no cover`. A line that cannot be reached is dead code — delete it instead.
  Several branches in this codebase turned out to be exactly that.
- An abstract method's body should `raise NotImplementedError`, which is excluded by configuration, rather
  than `pass`, which is not.
- **A branch behind randomness is a coverage bug, not an exception.** It makes the gate pass or fail by
  chance. Patch the RNG, see [mocking](mocking.md).

## Scope

Business logic is **not** confined to `handlers/` — see [where code goes](app-layout.md) for the split.
Targeting only `handlers/` would look complete while missing roughly 45% of the logic, so measurement
covers `handlers/`, `services/`, `managers/`, `models/` and `domain/`.

Views **are** measured. They are thin enough that the one-test-per-view rule reaches 100% on its own, so
there is no reason to exempt them.

Excluded from measurement, and why:

| Excluded | Why |
|---|---|
| `*/migrations/*` | Generated |
| `*/messages/*` | Dataclasses, no logic |
| `*/tests/*` | The tests themselves |
| `apps/config/*` | Settings, wsgi/asgi |
| `*/admin.py`, `*/apps.py` | Framework declarations |
