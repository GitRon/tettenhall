# Test Strategy: django-queuebie

Handlers are functions (message in → 0-n messages out), and `handle_message()` runs synchronously
inside **one** transaction. Most tests therefore need neither the queue nor a view.

Guiding principle: **branches unit, wiring integrated.**

Three failure classes, three tools:

- **Logic bugs** (wrong calculation, inverted condition, missed edge case) → unit test on the
  individual handler
- **Wiring bugs** (a handler emits a message nobody consumes) → registry test. Unit tests never
  catch these, no matter how many you write. The call chain only exists at runtime in the registry —
  no IDE, no type checker verifies it.
- **Message contract bugs** (a handler reads an attribute only one of its messages carries) →
  registry test as well. Handlers can be registered for several messages by stacking the decorators,
  and nothing connects that to the fields of those messages.

## Levels

| Level | Share | What |
|---|---|---|
| Handler unit | ~85% | Call the handler directly as a function |
| Flow | ~5–10% | Only where ordering or rollback matters. Doubles as the test for the action views |
| View (read-only) | ~5% | One per view: status code, context, savegame scoping |
| Registry | 4 tests | Discovery, dead commands, terminal events, attribute compatibility |

## What to test

### Handler unit tests (default)

- Import and call the handler **directly** — never through `handle_message()`. No registry, no queue
  loop.
- Handlers take their message **keyword-only**: `handler(context=my_message)`.
- Handlers return a **bare message**, a list, or `None` — `handle_message()` normalises all three.
  Assert on what the handler actually returns, so usually a bare message.
- Comparing messages by value works: they are `@dataclass(kw_only=True)`, and the random `uuid`
  lives on the non-dataclass `Message` base, so it is **not** a dataclass field and never breaks
  equality. `assert result == RestockTownShopItems(faction=faction, month=3)` is safe.
- **Most handler tests need `django_db` and factories.** Messages carry Django model instances, not
  IDs (`Faction` ~70×, `Warrior` ~54×, `Skirmish` ~36×), and handlers traverse relations
  (`context.warrior.faction`). Building unsaved instances works only for pure mapping handlers.
- A handler registered for **several** messages needs one test **per registered message**. That is
  where the contract bugs sit.
- At most two assertions per test: the returned message and the database side effect.
- One handler = one responsibility = 1–3 tests (happy path, one failure case, optionally one edge
  case).

### Flow tests (sparingly)

- Do **not** count by paths — that explodes combinatorially. Count by entry points: one test per
  view that kicks off the queue. There are **10 `handle_message()` call sites across 7 views**.
- Only write them where ordering or transaction behaviour genuinely matters.
- Assert on the end state only. Intermediate steps are already unit-tested.
- No mocking inside the chain — either a real flow or a unit test, nothing in between.
- This is the **only** level where strict mode's database blocker applies (see below).

### View tests

Views are thin: almost all are Django CBVs whose only logic is scoping a queryset to the current savegame
and assembling context. Keep the tests equally thin — **one test per view**, via the test client, with
`django_db`.

- Every view sits behind `LoginRequiredMiddleware`, so use a logged-in client fixture. Don't add a
  "redirects when anonymous" test per view; that is framework behaviour, and one test for it project-wide
  is enough.
- **Read views** (`DetailView`, `ListView`, `TemplateView`): assert the status code plus the one context
  key the view exists to provide, e.g. `assert response.context["warrior_list"] == [...]`.
- **Action views** (POST-only, calling `handle_message()`): these *are* the flow tests above. Assert the
  status code and the end state. Never mock `handle_message()` — that removes the only thing the test is
  for.
- **Savegame scoping deserves its own test** wherever a view overrides `get_queryset()`. Create an object
  in a second savegame and assert it is *not* reachable. This is the one view bug class that actually
  bites: everything else is a template detail, this one leaks another player's data.
- The UI is htmx-driven. Where a view sets `HX-Trigger`, assert the header is present — behaviour rides on
  it. Don't assert on the exact JSON payload.
- **Never assert on rendered HTML.** Status code, context and headers only. Template assertions break on
  every markup change and catch nothing.

### Registry tests

Four tests in `apps/common/tests/test_registry.py` cover all edges at once:

1. **Autodiscovery finds every handler** — every function decorated with `register_command` /
   `register_event` ends up in the registry.
2. **Every emitted command has a handler.** A command is an instruction, so one that nobody executes
   is *always* a bug. Deliberately **no allowlist**.
3. **Every emitted event is consumed or listed in `TERMINAL_MESSAGES`.** Events only announce a fact,
   so having no consumer can be legitimate.
4. **Handlers only read attributes all of their messages carry** — catches the multi-registration
   contract bug.

`TERMINAL_MESSAGES` is a deliberately maintained allowlist of events nobody is meant to consume
(currently 15). A new dead edge turns the test red without a single extra flow test.

#### Collect emitted messages from the code, not from annotations

Return annotations are useless here: all handlers annotate abstractly (`-> Event`,
`-> list[Event] | Event`, `-> Command`), and **zero** annotate concretely. Requiring concrete
annotations would mean touching 114 signatures — and an annotation can lie, while the code cannot.
The tests therefore parse the **actual message instantiations** out of the syntax tree.

One trap: the project mixes `from x import Command` with `from x import module` plus
`module.Command`. A name-based scan cannot tell those apart and reports confident false positives.
The scanner avoids this by resolving each name found in the tree **against the namespace of the
imported module**, which handles both spellings and needs no import bookkeeping:

```python
def _resolve(*, node: ast.expr, module) -> object | None:
    if isinstance(node, ast.Name):
        return getattr(module, node.id, None)

    if isinstance(node, ast.Attribute):
        parent = _resolve(node=node.value, module=module)

        return getattr(parent, node.attr, None) if parent is not None else None

    return None
```

Note that the registry keys the handlers by `message.module_path()` **strings**
(`"apps.faction.messages.commands.faction.RestockTownShopItems"`), not by classes, and the values are
`{"module": ..., "name": ...}` dicts rather than functions. Comparing classes against those keys
silently passes and tests nothing.

### Don't test

- Message dataclasses (no logic)
- The queue mechanics themselves (the package has its own test suite)
- Handler registration one by one — the registry tests suffice

## How to write a test

The suite runs on **pytest** + **pytest-django** with **factory_boy** for test data. No
`unittest.TestCase` anywhere — plain test functions and plain `assert` throughout.

### Layout

- Each app's `tests/` package mirrors the structure of its production code:
  `apps/item/services/generators/item.py` → `apps/item/tests/services/generators/test_item.py`.
- One test module per testee. If a module would have to hold tests for two testees, split it.
- **Always add `__init__.py`** to every `tests/` package and sub-package. Without it, two apps that both
  contain e.g. `tests/test_item.py` collide during collection and pytest fails on the duplicate module
  name.
- Order tests to reflect the order of functions and methods in the code under test.
- Group with plain functions. Use a `Test…` class only when several tests genuinely share fixtures, never
  just to namespace them.

### Naming

- `test_[testee]_[case]`, e.g. `test_handle_buy_item_for_faction_insufficient_silver`.
- Don't repeat the module name in the test name — it is already in the path.
- Avoid double underscores when testing protected functions.
- Use semantically useful names: `faction_with_two_warriors`, not `f1`.
- No type hints in variable names — avoid `warrior_qs`, `item_list`.

### Design

- Tests are atomic: one case per test. Avoid one large test covering every case.
- At least one test per function and one per branch — but don't overengineer, and one test per edge case,
  not more.
- Stick to **Arrange / Act / Assert**, separated by blank lines.
- Keep tests simple and readable: no loops, no clever abstractions, no helper indirection.
- Every test needs at least one assert. If the testee returns nothing and there is no other observable
  effect, assert `is None`.

### Assertions

- Use `pytest.raises(SomeError, match="expected message")` — never a bare `pytest.raises`, which also
  passes on the wrong error of the right type.
- Compare booleans identity-wise: `assert result is True` / `assert result is False`, not `assert result`
  — truthiness hides wrong types.
- Same for `None`: `assert result is None`.

### Test data

- **Never create model instances directly in a test** — no `Warrior.objects.create()`, no
  `Warrior(...).save()`. Always go through a factory.
- Factories live in `apps/<app>/tests/factories/<model>.py`, one factory per model, subclassing
  `factory.django.DjangoModelFactory`.
- Use `build()` where the object never has to hit the database, `create()` only where it must. Per the
  handler rules above, that is usually `create()`.
- Create in batches (`create_batch()`) rather than in loops when you need several objects.
- Keep shared setup minimal and function-scoped. The more objects a fixture creates, the less isolated
  the tests using it become.

### Mocking

**Mocking first-party code is strongly discouraged.** It is a last resort, not a technique to reach for
when a test is awkward to set up.

- A mock of our own code asserts that a particular function was called in a particular way — it pins the
  implementation, so the test goes green while the behaviour is broken and stays green through a refactor
  that breaks it. It tests the wiring you wrote down, not the wiring that runs.
- The usual reason to want one is expensive or fiddly setup. That is what factories are for. Build the real
  objects and call the real code.
- If you still think you need one, the more likely reading is that the testee does too much. Split it and
  test the parts directly.
- When you genuinely cannot avoid it, leave a comment saying why. A first-party mock without a stated
  reason is a review finding.

Mocking at the **boundary** is fine and expected: time, randomness, filesystem, network, third-party
calls. `apps/item/services/generators/` is random by nature — patch the RNG rather than asserting on
chance.

Import as `from unittest import mock` and always spell it `mock.patch(...)`, never
`from unittest.mock import patch`. One consistent spelling across the suite.

### Imports

- No local (function-level) imports in test files.

## Prerequisites and setup

Already in place:

- `[tool.pytest.ini_options]` in `pyproject.toml`, pointing at `apps.config.settings_test`
- `apps/config/settings_test.py` — keeps `QUEUEBIE_STRICT_MODE = True` and pins a dedicated
  `locmem` cache
- `conftest.py` — the `queuebie_registry` fixture, which resets the registry and its cache and then
  autodiscovers. The registry is a process-wide singleton **and** is cached in Django's cache
  backend, so without that reset registrations leak between tests.
- Factories under `apps/<app>/tests/factories/`

Concrete return annotations are **not** a prerequisite. Adding them is a worthwhile readability
change, but it is a separate refactor and must not block testing.

### What strict mode does and does not give you

`QUEUEBIE_STRICT_MODE = True` does two unrelated things:

- **At registration time** it rejects a command handler that lives in another app than its command.
  This applies whenever the handler module gets imported, so it holds in every test.
- **At dispatch time** `handle_message()` wraps event handlers in `BlockDatabaseAccess`.

The blocker is applied by `handle_message()`. Call a handler directly and it is gone, so it protects
**flow tests only**. That event handlers stay free of database writes has to be enforced by review —
it is not something unit tests get for free.

## Coverage

Business logic is **not** confined to `handlers/`:

| Layer | LOC |
|---|---|
| `handlers/` | 1930 |
| `services/` | 650 |
| `models/` | 602 |
| `managers/` | 352 |
| `domain/` | 37 |

With 10 handler → service call sites, covering only `handlers/` would look complete while missing
roughly 45% of the logic. Target `handlers/`, `services/`, `managers/`, `models/` and `domain/`;
exclude `messages/` and `migrations/`.

### 100% branch coverage

The gate is **100% branch coverage** over that scope — `branch = true` and `fail_under = 100` in
`pyproject.toml`. Statement coverage alone is not enough: it counts an `if` as covered once the body has
run, so a missing `else` and an unexercised loop-exit both pass unnoticed. Branch coverage is what makes
"one test per branch" above verifiable instead of aspirational.

Run it with `pytest --cov`.

Until the suite is complete this gate fails by design. That is the ratchet working, not a
misconfiguration — don't lower `fail_under` to turn a red run green.

Views **are** measured. They are thin enough that the one-test-per-view rule above reaches 100% on its
own, so there is no reason to exempt them.

Excluded from measurement, and why: `*/migrations/*` (generated), `*/messages/*` (dataclasses, no logic),
`*/tests/*` (the tests themselves), `apps/config/*` (settings, wsgi/asgi), `*/admin.py` and `*/apps.py`
(framework declarations).

## Effort and priorities

114 handlers × 1–3 tests ≈ 150–300 tests from a standing start. In order:

1. **The 4 registry tests.** Cheap, and they already found three real defects (below).
2. **The 29 handlers containing an `if`/`for`/comprehension.** This is where the logic bugs are.
3. **Flow tests** for the 10 entry points that matter.
4. **The ~85 trivial mappers, last.** The registry tests already cover most of their risk.

## Examples

Both examples are taken from the existing suite and pass.

```python
# Unit, no database: a pure mapping handler only reads from the message, so build() is enough
def test_handle_offer_new_quests_on_bulletin_board_maps_to_command():
    faction = FactionFactory.build()
    context = MonthPrepared(
        faction=faction, savegame=SavegameFactory.build(), training=TrainingFactory.build(), current_month=7
    )

    result = handle_offer_new_quests_on_bulletin_board(context=context)

    assert result == OfferNewQuestsOnBulletinBoard(faction=faction, month=7)


# Unit with database: a command handler that changes state, one test per branch
@pytest.mark.django_db
def test_handle_replenish_warrior_morale_fills_up_to_the_maximum():
    warrior = WarriorFactory(current_morale=5, max_morale=20)

    result = handle_replenish_warrior_morale(context=ReplenishWarriorMorale(warrior=warrior, month=3))

    assert result == WarriorMoraleReplenished(warrior=warrior, faction=warrior.faction, recovered_morale=15, month=3)
    warrior.refresh_from_db()
    assert warrior.current_morale == 20
```

## Defects found while writing these tests

All three were fixed; each is now covered by a registry test.

- **`DropWarriorItems`** — emitted by an event handler, but its command handler was commented out
  with a TODO. Dead edge. The TODO was right that `handle_distribute_loot()` supersedes it, so the
  command, its event and the emitting handler were removed.
- **`AddQuestToBulletinBoard`** — emitted on `QuestAccepted`, no handler anywhere. The emitting
  handler was named `handle_removed_accepted_quest_from_available_quests` but removed nothing;
  `handle_accept_quest` already takes the quest off the board. Implementing it literally would have
  put the just-accepted quest back on the board, so the stale path was removed.
- **`NewFactionCreated.current_month`** — three handlers are registered for both `MonthPrepared` and
  `NewFactionCreated` and read `context.current_month`, which only `MonthPrepared` carried. Creating
  a faction raised `AttributeError` and rolled the whole transaction back. `NewFactionCreated` now
  carries `current_month`, taken from the savegame.

The first two were unconsumed **commands** — which is why test 2 has no allowlist.
