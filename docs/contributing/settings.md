# Settings

- `apps/config/settings.py` — the application settings.
- `apps/config/settings_test.py` — the test settings, pointed at by `[tool.pytest.ini_options]` in
  `pyproject.toml`. It keeps `QUEUEBIE_STRICT_MODE = True` and pins a dedicated `locmem` cache.

## Queuebie settings

```python
QUEUEBIE_APP_BASE_PATH = BASE_DIR
QUEUEBIE_STRICT_MODE = True
```

`QUEUEBIE_APP_BASE_PATH` is where autodiscovery starts looking for handler modules.

`QUEUEBIE_STRICT_MODE` enforces the command→event / event→command contract. If a handler returns the
wrong message category, strict mode complains — fix the handler, don't disable the mode. What it does
and does not catch is in [strict mode](../patterns/strict-mode.md).
