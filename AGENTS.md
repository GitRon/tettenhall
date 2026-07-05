# Working with the message system (django-queuebie)

This project is built around **django-queuebie**, a lightweight command/event
bus. Almost every state change flows through it instead of happening directly in
a view or model. Read this before adding or editing business logic.

## The two message types

Everything is a *message*. There are exactly two kinds, both plain
`@dataclass(kw_only=True)` classes:

- **Command** (`queuebie.messages.Command`) — an *imperative instruction*:
  "do this". Named as a verb phrase: `UpgradeTownBuilding`, `CreateTransaction`,
  `DraftWarriorFromFyrd`. A command expresses intent that has not happened yet.
- **Event** (`queuebie.messages.Event`) — a *fact*, in past tense: "this
  happened". `TownBuildingUpgraded`, `WarriorRecruited`, `SkirmishFinished`.

```python
from dataclasses import dataclass
from queuebie.messages import Command

@dataclass(kw_only=True)
class UpgradeTownBuilding(Command):
    town: Town
    faction: Faction
    building_type: str
    new_level: int
    costs: int
    month: int
```

Messages carry already-resolved data (model instances, ints). Evaluate querysets
to lists *before* putting them on a message so downstream handlers don't hit the
DB unexpectedly — see `handle_faction_wins_skirmish` in
`apps/skirmish/handlers/commands/skirmish.py`, which wraps results in `list(...)`
with the comment *"We need to evaluate the QS to avoid hitting the DB in the
events"*.

## The golden rule of handlers

> **Command handlers do the work and emit Events.
> Event handlers react and emit Commands.**

- A **command handler** performs the actual state change (save models, run a
  service) and returns the Event(s) describing what happened.
- An **event handler** observes a fact and decides what *else* should now happen,
  returning Command(s). This is how one action fans out into others.

This keeps side effects in commands and reactions in events. Example chain:

```
UpgradeTownBuilding (cmd)
  └─ handle_upgrade_town_building  → mutates Town, saves, emits
       TownBuildingUpgraded (event)
         └─ handle_pay_building_costs_for_town_buildings → emits
              CreateTransaction (cmd)
                └─ ... and so on
```

The bus keeps draining the resulting messages until nothing new is produced.

## Handler signature & registration

Register with the decorator matching the message type; the handler takes the
message as a **keyword-only** `context` argument and returns messages (or `None`,
or a list):

```python
from queuebie import message_registry
from queuebie.messages import Command, Event

@message_registry.register_command(command=UpgradeTownBuilding)
def handle_upgrade_town_building(*, context: UpgradeTownBuilding) -> list[Event] | Event:
    setattr(context.town, context.building_type, context.new_level)
    context.town.save()
    return TownBuildingUpgraded(town=context.town, ...)   # command handler → Event

@message_registry.register_event(event=TownBuildingUpgraded)
def handle_pay_building_costs(*, context: TownBuildingUpgraded) -> Command | None:
    return CreateTransaction(faction=context.faction, amount=-context.costs, ...)  # event handler → Command
```

Conventions to keep:
- `context` is keyword-only (`*, context: ...`).
- Return type is `list[Event] | Event` (command handlers) or
  `list[Command] | Command` (event handlers); add `| None` when the handler may
  do nothing (e.g. `handle_draft_warrior_from_fyrd` bails when `fyrd_reserve <= 0`).
- Return a **list** to emit several messages at once (see
  `handle_assign_fighter_pairs` and `handle_restock_pub_mercenaries`).
- A single event can have multiple handlers in different apps — that's the point
  of the bus: `TownBuildingUpgraded` is emitted in `town` but also handled in
  `finance`.

## Where files go

Strict directory layout, discovered automatically by queuebie:

```
apps/<app>/messages/commands/<domain>.py   # Command dataclasses
apps/<app>/messages/events/<domain>.py     # Event dataclasses
apps/<app>/handlers/commands/<domain>.py   # functions handling Commands
apps/<app>/handlers/events/<domain>.py     # functions handling Events
```

- `<app>` is the Django app that *owns* the handler/message.
- `<domain>.py` is named after the app the message **originates from**, not where
  the handler lives. So `apps/finance/handlers/events/town.py` holds finance's
  reactions to events raised by the `town` app, and
  `apps/finance/handlers/events/skirmish.py` holds finance's reactions to
  skirmish events. This makes cross-app subscriptions easy to locate.
- Each `handlers/…` directory has an `__init__.py`; keep new modules importable
  so autodiscovery picks up the decorators.

## Dispatching a message (entry point)

Views (and other outer code) kick off a flow with `handle_message`:

```python
from queuebie.runner import handle_message

handle_message(
    UpgradeTownBuilding(town=town, faction=town.faction, building_type=building_type, ...)
)
```

Do **not** call handler functions directly and do **not** put multi-step
business logic in the view — validate input, build the initial Command, and hand
it to `handle_message`. Everything after that belongs in handlers/services.
Validation guards (can they afford it? already built this month?) currently live
in the view before dispatch (see `apps/town/views/town_upgrade.py`); there's a
standing TODO to move that into a validation service.

## Settings

In `apps/config/settings.py`:

```python
QUEUEBIE_APP_BASE_PATH = BASE_DIR
QUEUEBIE_STRICT_MODE = True
```

`STRICT_MODE` enforces the command→event / event→command contract and correct
typing. If you add a handler that returns the wrong message category, strict mode
will complain — fix the handler, don't disable the mode.

## Checklist for adding a new flow

1. Define the Command in `apps/<app>/messages/commands/<domain>.py`.
2. Write its command handler in `apps/<app>/handlers/commands/<domain>.py`; do
   the work, return an Event in `apps/<app>/messages/events/<domain>.py`.
3. For each reaction, add an event handler (in whichever app owns the reaction)
   returning further Commands.
4. Dispatch the initial Command from the view via `handle_message`.
5. Keep querysets evaluated to lists on messages; keep `context` keyword-only.

# Commit messages

Keep them short and to the point — a single capitalized subject line describing
what the commit does, no trailing period. Match the existing history:

- A noun phrase naming the change (`Hall effects`, `Display buildings`) or a
  past-tense/`Added …` phrase (`Added navbar todo`, `Fixed empty town shop bug`).
- Join two related changes with `&` (`UI & Validation`,
  `Min warrior stats & town shop fix`).
- No body, prefix, or issue tag unless a change genuinely needs explaining; then
  add a blank line and a couple of sentences.
