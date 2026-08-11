# Local setup

Tettenhall is a Django 5.2 application on Python 3.14 with a SQLite database.

Dependencies are managed with [uv](https://docs.astral.sh/uv/) from `pyproject.toml`. uv installs the
interpreter pinned in `.python-version` itself, so a matching Python does not have to be on the
system beforehand:

```bash
uv sync                                  # creates .venv and installs everything, dev group included
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Cultures and item types are reference data shipped as fixtures, and the item and warrior generators
query them by name — a database without them raises `RuntimeError` during generation:

```bash
uv run python manage.py loaddata culture itemtype
```

The test suite loads both automatically, see [test data](../patterns/testing-data.md).

## Running the tests

```bash
uv run pytest           # the suite
uv run pytest --cov     # with the coverage gate
```

See [testing strategy](../patterns/testing-strategy.md) before writing any test, and
[coverage](../patterns/coverage.md) for what the gate covers.

## Dependencies

`uv.lock` is committed and is the single source of truth for what gets installed:

```bash
uv add <package>              # runtime dependency
uv add --dev <package>        # development dependency
uv lock --upgrade             # refresh the lock within the declared constraints
```

`uv sync` re-reads the lock and matches the virtualenv to it exactly, removing anything that no
longer belongs. CI runs `uv sync --locked`, which fails on a lock file that has drifted from
`pyproject.toml` rather than re-resolving silently.
