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
- A single event can have multiple handlers **in different apps** — that is the point of the bus.
  `TownBuildingUpgraded` is emitted in `town` and also handled in `finance`.
- A handler can be registered for **several messages** by stacking the decorators. It may then only read
  attributes that *all* of those messages carry — nothing but the
  [registry tests](registry-tests.md) connects the two.
- Concrete return annotations are **not** required. Every handler annotates abstractly and none
  concretely; an annotation can lie while the code cannot, which is why tooling parses the actual
  instantiations instead.

## Reading from the database

Command handlers may query freely. Event handlers may not: strict mode wraps them in a database blocker
when they run through `handle_message()`. If a reaction needs to read something, emit a command and read
it in that command's handler — `handle_create_factions_for_new_savegame` exists for exactly this reason.
See [strict mode](strict-mode.md).

## See also

- [The message bus](message-bus.md)
- [Adding a new flow](adding-a-flow.md)
- [Where code goes](app-layout.md)
