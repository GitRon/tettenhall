# Linting and formatting

Two linters, both configured in `pyproject.toml`:

- **`ruff`** — formatting and lint rules, including import sorting.
- **`boa-restrictor`** — Ambient's own linter. Its `PBR`/`DBR` codes are registered with ruff via
  `lint.external`, so ruff does not flag their `noqa` comments as unknown.

Respect the **line length of 120**.

Both run as pre-commit hooks together with `django-upgrade` and `Djade`. A commit that reformats files
fails the first time and passes on the retry — stage the reformatted files and commit again.

## Per-file exceptions

`pyproject.toml` carries the exceptions rather than scattering `noqa` comments through the code:

- `**/__init__.py` may hold seemingly unused imports (`F401`).
- Views, admin, context processors and managers are exempt from boa-restrictor's keyword-only argument
  rules (`PBR001`/`PBR002`) — framework signatures are positional.
- `conftest.py` and everything under `*/tests/*` are exempt from `PBR001`, because pytest injects
  fixtures as positional arguments and keyword-only signatures are therefore impossible.

Add an exception here with a comment saying why, rather than silencing a rule inline.
