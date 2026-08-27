# The message bus

The project is built around **[django-queuebie](https://pypi.org/project/django-queuebie/)**, a
lightweight command/event bus. Almost every state change flows through it instead of happening directly
in a view or model.

## The two message types

Everything is a *message*. There are exactly two kinds, both plain `@dataclass(kw_only=True)` classes:

- **Command** (`queuebie.messages.Command`) — an *imperative instruction*: "do this". Named as a verb
  phrase: `UpgradeTownBuilding`, `CreateTransaction`, `DraftWarriorFromFyrd`. A command expresses intent
  that has not happened yet.
- **Event** (`queuebie.messages.Event`) — a *fact*, in past tense: "this happened".
  `TownBuildingUpgraded`, `WarriorRecruited`, `SkirmishFinished`.

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

Messages carry already-resolved data — model **instances**, not IDs. Evaluate querysets to lists *before*
putting them on a message so downstream handlers don't hit the database unexpectedly; see
`handle_faction_wins_skirmish` in `apps/skirmish/handlers/commands/skirmish.py`, which wraps its results
in `list(...)` with the comment *"We need to evaluate the QS to avoid hitting the DB in the events"*.

## The golden rule

> **Command handlers do the work and emit Events.
> Event handlers react and emit Commands.**

This keeps side effects in commands and reactions in events. One action fans out into others:

```
UpgradeTownBuilding (cmd)
  └─ handle_upgrade_town_building  → mutates Town, saves, emits
       TownBuildingUpgraded (event)
         └─ handle_pay_building_costs_for_town_buildings → emits
              CreateTransaction (cmd)
                └─ ... and so on
```

The bus keeps draining the resulting messages until nothing new is produced, all inside **one**
transaction.

## Dispatching (the entry point)

Views and other outer code kick off a flow with `handle_message`:

```python
from queuebie.runner import handle_message

handle_message(
    UpgradeTownBuilding(town=town, faction=town.faction, building_type=building_type, ...)
)
```

Do **not** call handler functions directly outside tests, and do **not** put multi-step business logic in
the view — validate the input, build the initial Command, and hand it to `handle_message`. Everything
after that belongs in handlers and services.

Validation guards (can they afford it? already built this month?) currently sit in the view before
dispatch, see `apps/town/views/town_upgrade.py`. There is a standing TODO to move them into a validation
service.

## When a side effect actually lands

The bus drains **FIFO**, and a handler's return value goes on the *back* of the queue. That gives one rule
worth knowing before you reason about what a handler can see:

> A command handler's own writes land immediately. Anything reached **through an event it returns** lands
> only after every message already queued has been handled.

So a handler that writes a row and a handler that *asks another app* to write one are not comparable in
timing, even when they sit side by side. Compare the two halves of the monthly salary run:

```
FactionMonthPrepared (evt)
  ├─ handle_pay_monthly_warrior_salaries_for_new_month → PayMonthlyWarriorSalaries (cmd) ─┐
  ├─ handle_earn_monthly_faction_income_for_new_month  → EarnMonthlyFactionIncome (cmd) ──┤ one batch,
  └─ handle_consider_fyrd_draft_for_new_month          → ConsiderFyrdDraft (cmd) ─────────┘ in order

PayMonthlyWarriorSalaries → handle_warrior_monthly_salaries
    writes warrior.unpaid_months          ← visible to the very next command
    returns MonthlyWarriorSalariesPaid    ← queued behind the whole batch
      └─ CreateTransaction (cmd) → the ledger row, later still
```

`handle_consider_fyrd_draft` runs last in that batch and still reads the balance the **month opened
with**, because the salary row does not exist yet. `unpaid_months`, written synchronously one command
earlier, it does see — which is why the recovery sweeps genuinely depend on being declared after the
salary run, and a flow test on `FinishMonthView` pins that.

Two things follow:

- **Declaration order buys you synchronous writes only.** Reordering handlers cannot change when a
  transaction, a log line or anything else routed through an event becomes visible.
- **A comment claiming otherwise is not evidence.** Several in this codebase asserted that registration
  order was what billed wages before income; the conclusion held and the stated reason did not. Read
  `queuebie/runner.py` — it is 60 lines — or assert the registry order in a shell, rather than trusting
  the nearest comment.

If a decision genuinely needs post-batch state, it cannot live in that batch. Move it behind the event
whose handler writes what you need to read.

## See also

- [Writing a handler](handlers.md)
- [Adding a new flow](adding-a-flow.md)
- [Strict mode](strict-mode.md)
- [Registry tests](registry-tests.md) — how dead edges in the chain are caught
