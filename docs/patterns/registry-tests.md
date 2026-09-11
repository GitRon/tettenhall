# Registry tests

Six tests in `apps/warband/tests/architecture/test_registry.py` cover every edge of the
[message bus](message-bus.md) at once. Unit tests can only ever verify a single handler; whether the
handlers form a chain is decided at runtime by the registry, so neither the IDE nor a type checker notices
when a message is emitted that nobody consumes.

They sit beside the other whole-tree tests in `apps/warband/tests/architecture/`. Every one of those
that walks the Python tree finds its input through `discovery.py` rather than a glob of its own. That module reads
queuebie's own exclusion setting to decide where handlers can live, so a test cannot quietly disagree
with what the bus actually imports — and the three that used to carry a private copy disagreed on glob
depth and on whether `__init__.py` counts, which is how a view in a `views/` package came to be checked
for savegame scoping and skipped by the finished-savegame guard.

1. **Autodiscovery finds every handler** — every function decorated with `register_command` /
   `register_event` ends up in the registry.
2. **Every emitted command has a handler.** A command is an instruction, so one that nobody executes is
   *always* a bug. Deliberately **no allowlist**.
3. **Every command has exactly one handler.** A command names the one piece of work it wants done, so a
   second handler on it is a second answer to a question that has one — and the two run in registration
   order, both against a message that reads like an instruction to one of them. Events are the message
   type that fans out, see [writing a handler](handlers.md).
4. **Every emitted event is consumed or listed in `TERMINAL_MESSAGES`.** Events only announce a fact, so
   having no consumer can be legitimate.
5. **Handlers only read attributes all of their messages carry** — catches the multi-registration contract
   bug, where a handler stacked on two decorators reads a field only one of the messages has.
6. **A command is handled in the module named after the one defining it.** Which module a message
   belongs in is a judgement call about its subject, see [where code goes](app-layout.md); that the
   command and its handler agree on the answer is not. Autodiscovery walks directories, so a command
   handled two modules away wires up and runs identically — this is the only thing that notices.

`TERMINAL_MESSAGES` is a deliberately maintained allowlist of events nobody is meant to consume. A new
dead edge turns the test red without a single extra flow test.

## Collect emitted messages from the code, not from annotations

Return annotations are useless here: all handlers annotate abstractly (`-> Event`,
`-> list[Event] | Event`, `-> Command`) and **zero** annotate concretely. Requiring concrete annotations
would mean touching 114 signatures — and an annotation can lie, while the code cannot. The tests therefore
parse the **actual message instantiations** out of the syntax tree.

One trap: the project mixes `from x import Command` with `from x import module` plus `module.Command`. A
name-based scan cannot tell those apart and reports confident false positives. The scanner avoids this by
resolving each name found in the tree **against the namespace of the imported module**, which handles both
spellings and needs no import bookkeeping:

```python
def _resolve(*, node: ast.expr, module) -> object | None:
    if isinstance(node, ast.Name):
        return getattr(module, node.id, None)

    if isinstance(node, ast.Attribute):
        parent = _resolve(node=node.value, module=module)

        return getattr(parent, node.attr, None) if parent is not None else None

    return None
```

Note that the registry keys handlers by `message.module_path()` **strings**
(`"apps.warband.faction.messages.commands.item.RestockTownShopItems"`), not by classes, and the values are
`{"module": ..., "name": ...}` dicts rather than functions. Comparing classes against those keys silently
passes and tests nothing.

## Defects these tests found

Writing them surfaced three real defects, all since fixed. Each is now covered by one of these tests.

- **`DropWarriorItems`** — emitted by an event handler, but its command handler was commented out with a
  TODO. Dead edge. The TODO was right that `handle_distribute_loot()` supersedes it, so the command, its
  event and the emitting handler were removed.
- **`AddQuestToBulletinBoard`** — emitted on `QuestAccepted`, no handler anywhere. The emitting handler was
  named `handle_removed_accepted_quest_from_available_quests` but removed nothing;
  `handle_accept_quest` already takes the quest off the board. Implementing it literally would have put the
  just-accepted quest back on the board, so the stale path was removed.
- **`NewFactionCreated.current_month`** — three handlers are registered for both `MonthPrepared` and
  `NewFactionCreated` and read `context.current_month`, which only `MonthPrepared` carried. Creating a
  faction raised `AttributeError` and rolled the whole transaction back. `NewFactionCreated` now carries
  the month, taken from the savegame.

The first two were unconsumed **commands**, which is why test 2 has no allowlist.
