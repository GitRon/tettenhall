# Testing strategy

**This is the single source of truth for what to test.** Do not infer the conventions from whatever tests
happen to be nearby, and do not fall back on generic Django testing habits — this project deviates from
them deliberately.

Handlers are functions (message in → 0-n messages out), and `handle_message()` runs synchronously inside
**one** transaction. Most tests therefore need neither the queue nor a view.

Guiding principle: **branches unit, wiring integrated.**

Three failure classes, three tools:

- **Logic bugs** (wrong calculation, inverted condition, missed edge case) → unit test on the individual
  handler.
- **Wiring bugs** (a handler emits a message nobody consumes) → [registry test](registry-tests.md). Unit
  tests never catch these, no matter how many you write: the call chain only exists at runtime in the
  registry, and no IDE and no type checker verifies it.
- **Message contract bugs** (a handler reads an attribute only one of its messages carries) →
  [registry test](registry-tests.md) as well.

## Levels

| Level | Share | What |
|---|---|---|
| Handler unit | ~85% | Call the handler directly as a function |
| Flow | ~5–10% | Only where ordering or rollback matters. Doubles as the test for the action views |
| View (read-only) | ~5% | One per view: status code, context, savegame scoping |
| Registry | 4 tests | Discovery, dead commands, terminal events, attribute compatibility |

## Handler unit tests (the default)

- Import and call the handler **directly** — never through `handle_message()`. No registry, no queue loop.
- Handlers take their message **keyword-only**: `handler(context=my_message)`.
- Handlers return a bare message, a list, or `None`. Assert on what the handler actually returns, so
  usually a bare message.
- Comparing messages by value works: they are `@dataclass(kw_only=True)`, and the random `uuid` lives on
  the non-dataclass `Message` base, so it is **not** a dataclass field and never breaks equality.
  `assert result == RestockTownShopItems(faction=faction, month=3)` is safe.
- **Most handler tests need `django_db` and factories.** Messages carry Django model instances, not IDs
  (`Faction` ~70×, `Warrior` ~54×, `Skirmish` ~36×), and handlers traverse relations
  (`context.warrior.faction`). Building unsaved instances works only for pure mapping handlers.
- A handler registered for **several** messages needs one test **per registered message**. That is where
  the contract bugs sit.
- At most two assertions per test: the returned message and the database side effect.
- One handler = one responsibility = 1–3 tests (happy path, one failure case, optionally one edge case).

## Flow tests (sparingly)

- Do **not** count by paths — that explodes combinatorially. Count by entry points: one test per view that
  kicks off the queue. There are **11 `handle_message()` call sites across 8 views**.
- Only write them where ordering or transaction behaviour genuinely matters.
- Assert on the end state only. Intermediate steps are already unit-tested.
- No mocking inside the chain — either a real flow or a unit test, nothing in between.
- This is the **only** level where [strict mode](strict-mode.md)'s database blocker applies.

## View tests

Views are thin: almost all are Django CBVs whose only logic is scoping a queryset to the current savegame
and assembling context. Keep the tests equally thin — **one test per view**, via the test client, with
`django_db`.

- Every view sits behind `LoginRequiredMiddleware`, so use the logged-in client fixture. Don't add a
  "redirects when anonymous" test per view; that is framework behaviour, and one project-wide test for it
  is enough.
- **Read views** (`DetailView`, `ListView`, `TemplateView`): assert the status code plus the one context
  key the view exists to provide, e.g. `assert response.context["warrior_list"] == [...]`.
- **Action views** (POST-only, calling `handle_message()`): these *are* the flow tests above. Assert the
  status code and the end state. Never mock `handle_message()` — that removes the only thing the test is
  for.
- **Savegame scoping deserves its own test** wherever a view overrides `get_queryset()`. Create an object
  in a second savegame and assert it is *not* reachable. See [savegame scoping](savegame-scoping.md).
- The UI is htmx-driven. Where a view sets `HX-Trigger`, assert the header is present — behaviour rides on
  it. Don't assert on the exact JSON payload.
- **Never assert on rendered HTML.** Status code, context and headers only. Template assertions break on
  every markup change and catch nothing.

## Don't test

- Message dataclasses (no logic)
- The queue mechanics themselves (the package has its own test suite)
- Handler registration one by one — the [registry tests](registry-tests.md) suffice

## Examples

Both are taken from the existing suite and pass.

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

## See also

- [Test conventions](testing-conventions.md) — layout, naming, assertions
- [Test data](testing-data.md) — factories and reference data
- [Mocking](mocking.md)
- [Coverage](coverage.md)
- [Registry tests](registry-tests.md)
