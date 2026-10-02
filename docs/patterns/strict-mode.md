# Strict mode

`QUEUEBIE_STRICT_MODE = True` holds in `apps/config/settings.py` **and** in
`apps/config/settings_test.py`. It does two unrelated things.

## At registration time

It rejects a command handler whose **scope** differs from its command's. A scope is the package owning
the `handlers/` or `messages/` directory a module sits in — here, the topic package. So
`apps/warband/faction/handlers/commands/item.py` may handle commands from
`apps/warband/faction/messages/`, and is refused a command out of `apps/warband/skirmish/messages/`:

```
Command "AddItemToTownShop" (scope "apps.warband.faction") cannot be handled by
"handle_add_item_to_town_shop" (scope "apps.warband.skirmish").
```

This applies whenever the handler module is imported, so it holds in every test too.

The check is on `register_command` only. Events are deliberately not scope-checked — crossing topics
is what events are for, see [writing a handler](handlers.md).

A command defined outside any `messages/` directory has its full module path as its scope, which only
a handler in that very module could share. Keep commands in a `messages/` directory.

## At dispatch time

`handle_message()` wraps event handlers in `BlockDatabaseAccess`.

The blocker patches the cursor, so it blocks **reads as well as writes**: any query inside an event
handler fails. That includes the queries nobody wrote down: a queryset iterated, a reverse relation
followed (`warrior.quest_contracts`), a `.all()` on a many-to-many. So messages carry lists, never
querysets, and whatever an event handler needs off a relation is resolved by the command handler that
raised the event and put on it as a field — see [the message bus](message-bus.md#the-two-message-types).

A read that works in a flow can still be one. Django caches a related object on the instance that loaded
it, so an event handler following a relation passes as long as the command handler upstream happened to
touch the same relation on the same instance, and breaks the day either side changes.

## What it does not give you

The blocker is applied by `handle_message()`. **Call a handler directly and it is gone**, so it protects
[flow tests](testing-strategy.md) only. That event handlers stay free of database access has to be
enforced by review — it is not something unit tests get for free.

## See also

- [Writing a handler](handlers.md) — how to move a read into a command handler
- [Settings](../contributing/settings.md)
