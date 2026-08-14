# Settings

- `apps/config/settings.py` — the application settings.
- `apps/config/settings_test.py` — the test settings, pointed at by `[tool.pytest.ini_options]` in
  `pyproject.toml`. It keeps `QUEUEBIE_STRICT_MODE = True` and pins a dedicated `locmem` cache.
- `apps/config/settings_smoke.py` — used when a browser drives the app for a content review. Identical to
  the application settings except for the database, which comes from `SMOKE_DB_PATH` so a smoke run plays
  on a throwaway file instead of the development savegames. Nothing else is relaxed: a content review is
  only worth its wall-clock if the app under the browser is the real one.

## Queuebie settings

```python
QUEUEBIE_APP_BASE_PATH = BASE_DIR
QUEUEBIE_STRICT_MODE = True
```

`QUEUEBIE_APP_BASE_PATH` is where autodiscovery starts looking for handler modules.

`QUEUEBIE_STRICT_MODE` enforces the command→event / event→command contract. If a handler returns the
wrong message category, strict mode complains — fix the handler, don't disable the mode. What it does
and does not catch is in [strict mode](../patterns/strict-mode.md).
