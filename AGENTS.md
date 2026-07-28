# Agent guide

Tettenhall is a Django 5.2 browser game built around a CQRS-style message bus
([django-queuebie](https://pypi.org/project/django-queuebie/)). Python 3.12, dependencies via `pipenv`
(`Pipfile`), SQLite, ruff + boa-restrictor for linting.

## Project docs

Read these before working in the area they cover — they are normative, not background reading.

| Doc | Read it when |
|---|---|
| [`docs/testing_strategy.md`](docs/testing_strategy.md) | **Always, before writing or changing any test, factory, fixture or test setting.** |
| [`docs/message_system.md`](docs/message_system.md) | **Always, before adding or editing a message, a handler, or anything dispatched through the bus.** |

## Testing

**`docs/testing_strategy.md` is the single source of truth for tests.** Do not infer the conventions from
whatever tests happen to be nearby, and do not fall back on generic Django testing habits — this project
deviates from them deliberately. In particular the doc settles:

- **pytest + pytest-django + factory_boy.** Plain test functions, plain `assert`, no `unittest.TestCase`,
  no `setUpTestData`, no `self.assertEqual`.
- **Never create model instances directly in a test.** Factories only, in
  `apps/<app>/tests/factories/<model>.py`.
- **Mocking first-party code is strongly discouraged** — last resort, and it needs a comment saying why.
- **100% branch coverage** is the gate. Until the suite is complete it fails by design; never lower
  `fail_under` to make a red run green.
- Where the interesting bugs actually are (wiring and message-contract bugs, which no amount of unit
  testing catches) and the four registry tests that cover them.

Setup already in place: `[tool.pytest.ini_options]` and `[tool.coverage.*]` in `pyproject.toml`,
`apps/config/settings_test.py`, and the `queuebie_registry` fixture in the root `conftest.py`.

Run the suite with `pytest`, with coverage via `pytest --cov`.

## Architecture notes

**`docs/message_system.md` is the single source of truth for the bus** — the command/event contract, the
handler signature, the directory layout messages and handlers must follow, and the checklist for adding a
new flow. The points worth keeping in mind everywhere:

- Each app owns `messages/` (commands + events) and `handlers/` (`commands/`, `events/`). Business logic
  also lives in `services/`, `managers/`, `models/` and `domain/` — roughly 45% of it sits outside
  `handlers/`, so don't treat `handlers/` as the whole story.
- **Command handlers do the work and emit Events; event handlers react and emit Commands.**
- Handlers take their message **keyword-only**: `handle_something(context=my_message)`. They return a bare
  message, a list of messages, or `None`; `handle_message()` normalises all three.
- Messages are `@dataclass(kw_only=True)` and carry Django **model instances**, not IDs.
- `QUEUEBIE_STRICT_MODE = True`. It rejects cross-app command handler registration at import time, and
  blocks database access in event handlers — but only when they run through `handle_message()`, so calling
  a handler directly in a test bypasses that check.
- Concrete return annotations are *not* required; the registry tests parse actual message instantiations
  out of the syntax tree instead, because an annotation can lie and the code cannot.
- **A savegame has exactly one player.** Rival factions are NPCs, so a rival reading "another faction's"
  data is not a leak. The pub belongs to the player, which is why `handle_add_warrior_to_pub` targets
  `savegame.player_faction` deliberately. `Transaction.for_savegame()` follows the same rule and filters
  `faction__player_savegame` — only the player faction's money counts.

## Conventions

- `ruff` and `boa-restrictor` are configured in `pyproject.toml`; respect the line length of 120.
- Settings live in `apps/config/settings.py`, test settings in `apps/config/settings_test.py`.

### Commit messages

Keep them short and to the point — a single capitalized subject line describing what the commit does, no
trailing period. Match the existing history:

- A noun phrase naming the change (`Hall effects`, `Display buildings`) or a past-tense/`Added …` phrase
  (`Added navbar todo`, `Fixed empty town shop bug`).
- Join two related changes with `&` (`UI & Validation`, `Min warrior stats & town shop fix`).
- No body, prefix, or issue tag unless a change genuinely needs explaining; then add a blank line and a
  couple of sentences.
