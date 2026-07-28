# Test data

- **Never create model instances directly in a test** — no `Warrior.objects.create()`, no
  `Warrior(...).save()`. Always go through a factory.
- Factories live in `apps/<app>/tests/factories/<model>.py`, one factory per model, subclassing
  `factory.django.DjangoModelFactory`.
- Use `build()` where the object never has to hit the database, `create()` only where it must. Per the
  [handler rules](testing-strategy.md), that is usually `create()`.
- Create in batches (`create_batch()`) rather than in loops when you need several objects.
- Keep shared setup minimal and function-scoped. The more objects a fixture creates, the less isolated the
  tests using it become.

## Mandatory relations belong in the factory

A factory has to produce a *valid* domain object. `FactionFactory` therefore carries a
`RelatedFactory` for the town, because every faction owns exactly one and several handlers read
`faction.town` — see [town buildings](town-buildings.md).

Reach through it to set up a case rather than building the related object separately:

```python
FactionFactory(town__marketplace=2)      # a faction whose town has a trading post
FactionFactory(town=None)                # no town at all
WarriorFactory(faction__town__sanctuary=3)
```

`RelatedFactory` is skipped for `build()`, so pure mapping tests stay database-free.

## Reference data is the one exception

`Culture` and `ItemType` are lookup tables, not test data. They ship as fixtures
(`apps/faction/fixtures/culture.json`, `apps/item/fixtures/itemtype.json`) and every environment has them.
The generators query them — `FyrdItemGenerator` even filters weapons by name — so without them item and
warrior generation raises `RuntimeError`.

The root `conftest.py` loads both fixtures once per session via `django_db_setup`. **Don't hand-seed
cultures or item types**, and don't build look-alikes: a test that creates its own `ItemType(name="Spear")`
passes while asserting nothing about the data the game actually ships.

Use a factory for these two only when a test needs a *specific* variant the fixtures don't contain (a
fallback type, say). Note the flip side: reference tables are **not empty** in tests, so never assume a
query over them returns exactly the rows you created. A handler picking
`Culture.objects.all().order_by("?").first()` really does return one of five.

## Fixtures in the root conftest

- `user` — a user.
- `logged_in_client` — test client with an authenticated user, since every view sits behind
  `LoginRequiredMiddleware`.
- `current_savegame` — the active savegame of the logged-in user, **including** its player faction. Three
  context processors run on every authenticated render and dereference
  `current_savegame.player_faction`, so anything rendering a template needs this rather than a bare
  savegame.
- `savegame_without_player_faction` — the reachable state before the faction exists; every view scoped to
  the player faction has to narrow to nothing here instead of answering with a 500.
- `queuebie_registry` — a freshly autodiscovered handler registry.
