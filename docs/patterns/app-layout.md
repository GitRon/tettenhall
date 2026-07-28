# Where code goes

Each Django app under `apps/` owns its own messages and handlers, in a strict layout that queuebie
discovers automatically:

```
apps/<app>/messages/commands/<domain>.py   # Command dataclasses
apps/<app>/messages/events/<domain>.py     # Event dataclasses
apps/<app>/handlers/commands/<domain>.py   # functions handling Commands
apps/<app>/handlers/events/<domain>.py     # functions handling Events
```

- `<app>` is the Django app that *owns* the handler or message.
- `<domain>.py` is named after the app the message **originates from**, not where the handler lives. So
  `apps/finance/handlers/events/town.py` holds finance's reactions to events raised by the `town` app,
  and `apps/finance/handlers/events/skirmish.py` holds its reactions to skirmish events. This makes
  cross-app subscriptions easy to locate.
- Every `handlers/…` directory needs an `__init__.py`; keep new modules importable so autodiscovery
  picks up the decorators.

## Business logic is not only in handlers

Roughly 45% of the logic sits outside `handlers/`, so don't treat it as the whole story:

| Layer | LOC |
|---|---|
| `handlers/` | 1930 |
| `services/` | 650 |
| `models/` | 602 |
| `managers/` | 352 |
| `domain/` | 37 |

Handlers call into `services/` in 10 places. Anything measured or reviewed has to cover `services/`,
`managers/`, `models/` and `domain/` as well — see [coverage](coverage.md).

Game-balance numbers are a special case and live in `apps/town/buildings/`, see
[town buildings](town-buildings.md).
