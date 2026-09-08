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

## Creating a record

**A record of something that happened is written through `Model.objects.create_record()`. Everything
else is created with `objects.create()` at the call site.**

A record is a row nobody edits afterwards: a ledger entry, a log line, a blow struck, a spoil taken. It
is written once by whatever the game just did and read back as history — `PlayerMonthLog`,
`Transaction`, `BattleHistory`, `SkirmishBlow`, `SkirmishSpoil`. A game object is the other kind, and
the player goes on acting on it for the rest of the savegame: a `Faction`, a `Town`, an `Item`, a
`Warrior`, a `Skirmish`.

The split earns its keep on the first kind, because the columns of a record often follow from each
other and the producer should not be able to set them against each other.
`PlayerMonthLog.objects.create_record()` takes a `kind` and derives the `category` a line is filed
under (`apps/month/managers/player_month_log.py:16`); `SkirmishBlow.objects.create_record()` takes two
rolls and unpacks them into the columns that survive a restart
(`apps/skirmish/managers/skirmish_blow.py:19`). A record whose columns are all handed in still goes
through the manager, so that "where is a row of this written" has one answer per model rather than one
per column.

A game object is created where the thing that decides its values already stands. The item generator
computes condition, modifier and price and then calls `Item.objects.create()` with them
(`apps/item/services/generators/item/base.py:103`) — moving the call behind a manager method would move
six keyword arguments and none of the deciding.

The method is called `create_record` whatever the model is. The model is the manager's already, so its
name does not go in the method's.
