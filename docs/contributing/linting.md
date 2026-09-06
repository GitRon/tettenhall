# Linting and formatting

Two linters, both configured in `pyproject.toml`:

- **`ruff`** — formatting and lint rules, including import sorting.
- **`boa-restrictor`** — Ambient's own linter. Its `PBR`/`DBR` codes are registered with ruff via
  `lint.external`, so ruff does not flag their `noqa` comments as unknown. It also runs this project's
  own rules, see below.

Respect the **line length of 120**.

Both run as pre-commit hooks together with `django-upgrade` and `Djade`. A commit that reformats files
fails the first time and passes on the retry — stage the reformatted files and commit again.

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
