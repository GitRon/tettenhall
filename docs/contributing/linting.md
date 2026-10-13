# Linting and formatting

Four linters, all configured in `pyproject.toml`:

- **`ruff`** — formatting and lint rules, including import sorting.
- **`boa-restrictor`** — Ambient's own linter. Its `PBR`/`DBR` codes are registered with ruff via
  `lint.external`, so ruff does not flag their `noqa` comments as unknown. It also runs this project's
  own rules, see below.
- **`import-linter`** — the direction of dependency between the apps, see below.
- **`complexipy`** — the cognitive complexity of every function, see below.

Respect the **line length of 120**.

ruff, boa-restrictor and complexipy run as pre-commit hooks together with `django-upgrade` and `Djade`. A
commit that reformats files fails the first time and passes on the retry — stage the reformatted files
and commit again.

## Cognitive complexity

complexipy scores every function the way [cognitive
complexity](https://www.sonarsource.com/resources/cognitive-complexity/) does — each branch and loop
costs a point, plus one more per level of nesting it sits at — and fails above **15**. The paths and
the limit live under `[tool.complexipy]`; the hook checks the staged files, and CI's pre-commit job checks
all of them. Production code, tests and scripts are held to the same limit.

Over the limit, look for the step the function already takes without naming it: the walk for one item of
a loop over several, a check that is a question of its own, a block written out twice. Pull that out
under a name that says what it does. A split that only exists to move the number — a helper that takes
half of a decision and hands back a flag for the other half — makes the code worse, and the score is
not worth it.

When a function is genuinely one indivisible piece of logic, mark it with `# noqa: complexipy` on the
`def` line and a comment above saying why. That is the one inline exception this page allows: complexipy
can only exclude whole paths, not single functions.

Run it locally with `uvx complexipy@8.0.1`, which reads the paths and the limit from `pyproject.toml`.
`--failed` lists only what is over the limit.

## Import boundaries

`lint-imports` checks the contracts under `[tool.importlinter]` and runs in CI next to the test job,
not as a pre-commit hook — it builds the whole import graph, which is too slow for a commit.

Four contracts:

- **No satellite may import `apps.warband`.** A satellite is domain-independent by definition, and
  the direction of dependency is the entire reason for splitting one out. Without the contract, a
  game-balance decision or the navbar's resource bar slips into `common` and nothing says so.
- **No name provider may import `apps.common`.** `apps.faker_frisian`, `apps.faker_gaelic` and
  `apps.faker_old_english` are name providers and nothing else, which is what keeps each liftable
  into a library of its own.
- **The three name providers are `independence`-checked against each other.** They share a shape and
  nothing more; a helper reached across would tie all three to whichever lifts out first. Frisian and
  Old English are the pair this is written for: their joining rules differ only in the endings, and
  restating them rather than sharing them is deliberate.
- **Neither app may import `apps.config`.** It is the settings package, not an app. Settings are read
  through `django.conf.settings`, which is lazy and which `override_settings` can reach; importing the
  module directly bypasses both and binds the value at import time.

There are deliberately **no contracts between the topic packages** inside `apps.warband`. They are meant
to be cheap to move, and the boundary that does need enforcing — a command handler outside the scope of
its command — is queuebie's [strict mode](../patterns/strict-mode.md).

Run it locally with `uv run lint-imports`. A broken contract names the importing module and the line.

## Project rules

boa-restrictor runs project-owned rules alongside its built-ins. They live in `scripts/linting/`, are
registered by dotted path in `custom_rules` under `[tool.boa-restrictor]`, and carry the `TBR` prefix —
Tettenhall. `PBR` and `DBR` are reserved for boa-restrictor's own rules and are rejected at load time.
`TBR` is registered with ruff via `lint.external` like the other two.

A rule subclasses `boa_restrictor.common.rule.Rule`, sets `RULE_ID` (matching `^[A-Z]+\d+$`, or it can
never be silenced by a `noqa`) and `RULE_LABEL`, and implements `check()` returning `Occurrence`s built
with `self._build_occurrence(line_number=...)`. The source tree arrives already parsed.

| Rule | What |
|---|---|
| `TBR001` | Bans `from __future__ import annotations`. PEP 649 makes annotations lazy on 3.14, so the import does nothing — an unquoted forward reference resolves without it. |

boa-restrictor is a dev dependency as well as a pre-commit hook, because the rules' tests import `Rule`.
The two versions are pinned separately, in `pyproject.toml` and in `.pre-commit-config.yaml`; keep them
in step.

## Per-file exceptions

`pyproject.toml` carries the exceptions rather than scattering `noqa` comments through the code:

- **Ruff**
  - `**/__init__.py` may hold seemingly unused imports (`F401`), and so may `apps/warband/admin.py`,
    which imports the topic admins for their registrations.
  - `apps/config/settings_*.py` star-import the base settings (`F403`).
  - `scripts/playtest/__main__.py` imports after `django.setup()` (`E402`).
- **boa-restrictor**: wherever a framework calls our code, the signature is the framework's, and it
  passes arguments positionally.
  - Views (`*/views.py`, `*/views/*.py`) and `*/admin.py` are exempt from `PBR001` and `PBR002`.
  - Everything else below is exempt from `PBR001` only:
    - `*/mixins.py`
    - context processors (`*/context_processors.py`, `*/context_processors/*.py`)
    - template tags and filters (`*/templatetags/*.py`)
    - forms, fields and widgets (`*/forms/*.py`)
    - validators (`*/validators.py`)
    - management commands (`*/management/commands/*.py`)
    - migrations (`*/migrations/*.py`)
    - `apps/config/settings.py`, for the django-axes callables
    - `tools/portrait_alignment/serve.py`, for the `http.server` hook
  - `*/managers/*.py` are exempt from `PBR002`.
  - `conftest.py` and everything under `*/tests/*` are exempt from `PBR001`, because pytest injects
    fixtures as positional arguments, so keyword-only signatures are impossible.

Add an exception here with a comment saying why, rather than silencing a rule inline.
