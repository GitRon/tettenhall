# Writing a handler

Register with the decorator matching the message type. The handler takes the message as a
**keyword-only** `context` argument and returns messages, `None`, or a list:

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

## Conventions

- `context` is keyword-only (`*, context: ...`).
- Return type is `list[Event] | Event` for command handlers, `list[Command] | Command` for event
  handlers; add `| None` when the handler may do nothing (e.g. `handle_draft_warrior_from_fyrd` bails
  when `fyrd_reserve <= 0`).
- Return a **list** to emit several messages at once, see `handle_assign_fighter_pairs` and
  `handle_restock_pub_mercenaries`. `handle_message()` normalises a bare message, a list and `None`
  alike.
- A single event can have multiple handlers **in different topic packages** — that is the point of the
  bus, and the reason events are not scope-checked. `TownBuildingUpgraded` is emitted in `town` and also
  handled in `finance`. A *command* handler is scope-checked, see [strict mode](strict-mode.md).
- A **command has exactly one handler**, and the [registry tests](registry-tests.md) enforce it. A command
  names the one piece of work it wants done; a reaction that belongs to somebody else hangs off the event
  that handler returns. Fanning out is what events are for.
- A handler can be registered for **several messages** by stacking the decorators. It may then only read
  attributes that *all* of those messages carry — nothing but the
  [registry tests](registry-tests.md) connects the two.
- Concrete return annotations are **not** required. Every handler annotates abstractly and none
  concretely; an annotation can lie while the code cannot, which is why tooling parses the actual
  instantiations instead.

## Reading from the database

Command handlers may query freely. Event handlers may not: strict mode wraps them in a database blocker
when they run through `handle_message()`. If a reaction needs to read something, emit a command and read
it in that command's handler — `handle_prepare_month` exists for exactly this reason. See
[strict mode](strict-mode.md).

**Then emit facts, one per subject.** That command handler still emits events, like every other one:
fanning out into per-subject commands is the *event* handler's job. A command handler that raises commands
of its own is the golden rule broken, and the
[registry tests](registry-tests.md) fail on it.

| The fact you can name | The shape |
|---|---|
| The subject exists and something reached it | A read-only command → one event per subject → the reactions fan out. `handle_prepare_month`, `handle_prepare_faction_warriors_for_month` |
| The subject does not exist yet | The handler creates it and announces *it now exists*. A command that only plans the creation announces a plan, not a fact — `handle_create_factions_for_new_savegame` does the creating |
| The handler decomposes one order into several and writes nothing | It may emit commands — the one allowlisted case, and the allowlist wants a reason |

**The read belongs in the topic that owns what is read.** A dispatcher needs to know whom to notify, not
what each recipient contains: `handle_prepare_month` queries which factions are still in play, because it
is deciding who gets a month, and stops there. *"A faction is responsible for its own roster plus the
prisoners it holds"* is a rule about factions and is read in `faction`.

Where the read stays unfiltered, that is deliberate rather than sloppy. `WarriorMonthPrepared` is a fact
because every living man raises one and the reactions do the filtering; a sweep that selected the wounded
could only announce a state somebody looked up.

Two smells that say the shape is wrong:

- **An event named `…Determined` or `…Found`.** It announces that a query returned, which is the handler's
  own bookkeeping rather than anything that happened.
- **A command with one emitter and one handler that exists only so another handler had somewhere to send
  work.** Fix the shape and it has no reason left to be a message.

## See also

- [The message bus](message-bus.md)
- [Adding a new flow](adding-a-flow.md)
- [Where code goes](app-layout.md)
