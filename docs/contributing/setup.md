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

Cultures, item types and quest names are reference data shipped as fixtures, and the item, warrior and
quest generators query them — a database without them raises `RuntimeError` during generation:

```bash
uv run python manage.py loaddata culture itemtype questname
```

The test suite loads all three automatically, see [test data](../patterns/testing-data.md).

## Frontend assets

The frontend dependencies come from npm and are managed with yarn. `node_modules/` is served directly
as a static root, so **without this step the app renders with no stylesheets and no htmx** — which
looks like a broken page but is in fact a broken install, since every control that posts a command goes
through htmx.

```bash
yarn install
yarn build:css                           # compiles assets/css/tailwind.css -> static/dist/tailwind.css
```

`static/dist/` is not in version control, so a fresh clone has to compile it once. Tailwind emits only
the utilities it finds in the templates under `apps/`, which means **the stylesheet has to be rebuilt
after a template gains a class it did not use before** — otherwise the class resolves to nothing and
the page silently loses that bit of layout. During development, leave the watcher running instead:

```bash
yarn watch:css
```

See [responsive layout](../patterns/responsive-layout.md) for what those classes are allowed to say.

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
