# Local setup

Tettenhall is a Django 5.2 application on Python 3.12 with a SQLite database.

Dependencies are managed with `pipenv` from the `Pipfile`:

```bash
pipenv install --dev
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser
pipenv run python manage.py runserver
```

Cultures and item types are reference data shipped as fixtures, and the item and warrior generators
query them by name — a database without them raises `RuntimeError` during generation:

```bash
pipenv run python manage.py loaddata culture itemtype
```

The test suite loads both automatically, see [test data](../patterns/testing-data.md).

## Running the tests

```bash
pipenv run pytest           # the suite
pipenv run pytest --cov     # with the coverage gate
```

See [testing strategy](../patterns/testing-strategy.md) before writing any test, and
[coverage](../patterns/coverage.md) for what the gate covers.
