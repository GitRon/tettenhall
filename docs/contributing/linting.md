# Linting and formatting

Three linters, all configured in `pyproject.toml`:

- **`ruff`** — formatting and lint rules, including import sorting.
- **`boa-restrictor`** — Ambient's own linter. Its `PBR`/`DBR` codes are registered with ruff via
  `lint.external`, so ruff does not flag their `noqa` comments as unknown. It also runs this project's
  own rules, see below.
- **`import-linter`** — the direction of dependency between the apps, see below.

Respect the **line length of 120**.

ruff and boa-restrictor run as pre-commit hooks together with `django-upgrade` and `Djade`. A commit
that reformats files fails the first time and passes on the retry — stage the reformatted files and
commit again.

## Import boundaries

`lint-imports` checks the contracts under `[tool.importlinter]` and runs in CI next to the test job,
not as a pre-commit hook — it builds the whole import graph, which is too slow for a commit.

Two contracts, both `forbidden`:

- **`apps.common` must not import `apps.warband`.** A satellite is domain-independent by definition, and
  the direction of dependency is the entire reason for splitting one out. Nothing enforced this before,
  which is how a game-balance decision and the navbar's resource bar came to live in `common`.
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

- `**/__init__.py` may hold seemingly unused imports (`F401`).
- Views, admin, context processors and managers are exempt from boa-restrictor's keyword-only argument
  rules (`PBR001`/`PBR002`) — framework signatures are positional.
- `conftest.py` and everything under `*/tests/*` are exempt from `PBR001`, because pytest injects
  fixtures as positional arguments and keyword-only signatures are therefore impossible.

Add an exception here with a comment saying why, rather than silencing a rule inline.
