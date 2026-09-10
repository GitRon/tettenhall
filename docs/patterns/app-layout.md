# Where code goes

**There are two Django apps: `apps.warband`, which is the game, and `apps.common`, which is not.** A
Django app is a unit of persistence and Django configuration — models, migrations, templates, template
tags, fixtures, admin — and not a unit of code organisation. The game's structure lives one level below
the app, in *topic packages*.

Everything in the app layer sits directly under `apps/`, so that directory lists the whole
architecture. Not all of it is an app: a satellite that owns no models and needs no Django
configuration is a plain package there, the way `config/` and the three name providers are, and stays
out of `INSTALLED_APPS`.

```
apps/
├── config/                      # the settings package, deliberately not an app
├── common/                      # a satellite: no domain concept, imports no domain code
├── faker_frisian/               # a satellite, and not an app: it registers with Faker, not Django
├── faker_gaelic/                # its sibling, for the Irish culture
├── faker_old_english/           # and for the Saxon one
└── warband/                     # the domain app
    ├── apps.py  urls.py  admin.py
    ├── migrations/              # one per change, for the whole game
    ├── models/__init__.py       # re-exports every model, which is what registers them
    ├── templates/<topic>/…
    ├── templatetags/  management/  fixtures/
    ├── tests/architecture/      # the meta-tests that check the whole tree at once
    └── faction/ skirmish/ warrior/ town/ quest/ item/ finance/ month/ …
```

## The app root is Django's, everything else is yours

Django looks exactly one fixed path into an app for each of the things it discovers, and never below
it. So these live at the app root and nowhere else — putting one in a topic package makes it vanish
with no error anywhere:

| At the app root | Because Django reads only |
|---|---|
| `migrations/` | `<app>/migrations/` |
| `models/__init__.py` | `<app>/models` — a model missing from it gets no table |
| `templates/` | `<app>/templates/` — one subdirectory per topic, named after it, plus `base.html` |
| `templatetags/` | `<app>/templatetags/` |
| `management/commands/` | `<app>/management/commands/` |
| `fixtures/` | `<app>/fixtures/` |
| `admin.py` | `<app>/admin.py` — hence the imports it collects |
| `apps.py`, `urls.py` | named from settings and the root urlconf |

Everything else — `handlers/`, `messages/`, `services/`, `managers/`, `models/*.py`, `views.py`,
`forms/`, `domain/`, `tests/` — belongs to a topic package. Topic packages are cheap to rename and
cheap to move; an app boundary is not, which is the whole reason there is only one.

## Messages and handlers

queuebie discovers handlers anywhere below the app root, so each topic keeps its own:

```
apps/warband/<topic>/messages/commands/<domain>.py   # Command dataclasses
apps/warband/<topic>/messages/events/<domain>.py     # Event dataclasses
apps/warband/<topic>/handlers/commands/<domain>.py   # functions handling Commands
apps/warband/<topic>/handlers/events/<domain>.py     # functions handling Events
```

- `<topic>` is the topic package that *owns* the handler or message. It is also the **scope** queuebie
  enforces: a command handler may only handle commands of its own topic, see
  [strict mode](strict-mode.md).
- **`<domain>.py` names whatever the topic package does not already name.** The path carries two
  coordinates, and the second one never repeats the first:

  | Directory | The topic package is | So `<domain>` is |
  |---|---|---|
  | `messages/commands/`, `messages/events/` | the origin — strict mode lets a topic raise only its own | the **subject**: the model the message is about |
  | `handlers/commands/` | the origin, again | whatever `messages/commands/` chose — the two modules **mirror** |
  | `handlers/events/` | the *reactor*, not the origin | the **originating topic** |

  Subject names are spelled as the model's module under `models/`, and a message about the topic's own
  central model lands in `<topic>.py`. So `apps/warband/item/messages/commands/item.py` holds
  `CreateItem` while `apps/warband/skirmish/messages/commands/transaction.py` holds
  `WarriorDropsSilver` — one topic, two subjects.

  Under `handlers/events/` the origin is what makes a cross-topic subscription findable:
  `apps/warband/finance/handlers/events/town.py` holds finance's reactions to events raised by the
  `town` topic. When a topic subscribes to its **own** events the origin only repeats the directory,
  so `<domain>` falls back to the subject — `apps/warband/skirmish/handlers/events/warrior.py`.

  The mirror in the second row is not a convention to remember: a
  [registry test](registry-tests.md) fails when a command and its handler sit in differently-named
  modules.
- Keep new modules importable so autodiscovery picks up the decorators. An `__init__.py` is no longer
  strictly required — Python treats the directory as a namespace package without one — but every
  existing `handlers/` directory has one and new ones should match.
- A directory named `tests`, `migrations`, `fixtures`, `templates`, `static`, `media`, `locale`,
  `node_modules` or `__pycache__` is skipped by autodiscovery, which is why the test mirror under
  `<topic>/tests/handlers/` never registers anything. Do not name a topic package after one of them.

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

Game-balance numbers are a special case and live in `apps/warband/town/buildings/`, see
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
under (`apps/warband/month/managers/player_month_log.py:16`); `SkirmishBlow.objects.create_record()` takes two
rolls and unpacks them into the columns that survive a restart
(`apps/warband/skirmish/managers/skirmish_blow.py:19`). A record whose columns are all handed in still goes
through the manager, so that "where is a row of this written" has one answer per model rather than one
per column.

A game object is created where the thing that decides its values already stands. The item generator
computes condition, modifier and price and then calls `Item.objects.create()` with them
(`apps/warband/item/services/generators/item/base.py:103`) — moving the call behind a manager method would move
six keyword arguments and none of the deciding.

The method is called `create_record` whatever the model is. The model is the manager's already, so its
name does not go in the method's.
