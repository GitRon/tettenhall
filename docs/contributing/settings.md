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
QUEUEBIE_LOGGER_NAME = "queuebie"
```

`QUEUEBIE_APP_BASE_PATH` is where autodiscovery starts looking for handler modules.

`QUEUEBIE_STRICT_MODE` enforces the command→event / event→command contract. If a handler returns the
wrong message category, strict mode complains — fix the handler, don't disable the mode. What it does
and does not catch is in [strict mode](../patterns/strict-mode.md).

`QUEUEBIE_LOGGER_NAME` names the logger the bus writes to. It is queuebie's own default, spelled out
here because `LOGGING` below has to name the same logger — and the two drifting apart is silent.

## Logging

One console handler, on the root logger, at `WARNING`. The bus logger runs at `DEBUG` while `DEBUG` is
on, so every message drained shows up with the handler it went to and the messages that handler
returned:

```
2026-09-07 10:14:22,001 DEBUG   queuebie: Handling command 'apps.month.messages.commands.month.PrepareMonth' (…) with handler 'handle_prepare_month'.
2026-09-07 10:14:22,004 DEBUG   queuebie: New messages: ["<class 'apps.month.messages.events.month.PlayerMonthPrepared'> (…)"]
```

That is the record of an ordering question — which handler's writes were visible to which — and it is
the cheapest answer to one, see [the message bus](../patterns/message-bus.md).

Autodiscovery writes to the same logger, so the first thing in the log of a fresh process is queuebie
registering every handler it found, one line each plus a dump of every message and the handlers it
maps to — a couple of hundred lines before the first message is drained. That is the registry, not the
queue.

Two things about the dict are deliberate rather than stylistic:

- **The `django` logger is listed with no handlers of its own.** Django applies its own configuration
  first and gives that logger a console handler without turning propagation off, so leaving it out
  would print every Django record twice — once there, once on the root handler. Listing it hands its
  records to the one console handler. It also drops `mail_admins` from that chain; the project
  configures neither `ADMINS` nor a mail backend.
- **The loggers below it come along.** `logging.config` resets every existing logger under a
  configured one, so naming `django` leaves `django.server` and `django.request` with no handler of
  their own and propagation on. The runserver request lines therefore arrive in the format above,
  timestamped and named, rather than in Django's `[server_time] message`.

An application logger is not part of this: nothing in `apps/` calls `getLogger`, and the record of what
the *game* did is the month log, not the console.
