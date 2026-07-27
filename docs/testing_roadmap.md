# Testing roadmap

Handover for continuing the test suite. Read
[`docs/testing_strategy.md`](testing_strategy.md) first — it is normative and this document
assumes it.

## Where things stand

Branch `feature/queuebie-test-foundation`, 17 commits, **187 tests green**, pre-commit clean.

Coverage is at **93%** against a `fail_under = 100` branch-coverage gate: **138 statements and 29
partial branches** remain. CI is red by design until that closes.

Done so far: the four registry tests, three architectural view-scoping tests, a factory per model,
handler tests for all 29 branching handlers, and one behaviour plus one scoping test for each of the
34 views, including flow tests that run the real queue.

Fifteen production defects were found and fixed along the way. Two were fatal — nobody could create
a savegame, and combat rolled back as soon as a warrior went down — and nine were cross-savegame
authorisation holes.

## What is left

Roughly in the order worth doing.

### 1. One open decision

`apps/quest/services/generators/quest.py:28` — `random.choice(faction_qs)` raises `IndexError` when
a savegame has no faction besides the player's, so that savegame can never finish a month. Line 20
has the same problem when `player_faction` is `None`. Only reachable in a degenerate savegame, since
bootstrap always creates 3–5 rivals. Decide: skip quest creation, allow a self-targeted quest, or
fail loudly. Then test it.

### 2. Services — the biggest gap, and the most logic per line

| File | Missing |
|---|---|
| `apps/skirmish/services/actions/risky_attack.py` | 15–24 |
| `apps/skirmish/services/actions/fast_attack.py` | 16, 21–31 |
| `apps/skirmish/services/actions/defensive_stance.py` | 19, 23 |
| `apps/skirmish/services/skirmish/assign_fighter_pairs.py` | 20–21 |
| `apps/skirmish/services/skirmish/damage.py` | 41 |
| `apps/item/services/generators/item/base.py` | 35, 46 |
| `apps/item/services/generators/item/fyrd.py` | 20 |

All combat and generation is random. Patch at the boundary (`random.gauss`, `random.randrange`,
`random.choice`) in the module where it actually runs — often the model or service, not the caller.
Never assert on chance.

### 3. Models, managers, domain

Mostly small: `apps/item/models/item.py` (50, 54, 58–63), `apps/training/models/training.py`
(43–48), `apps/skirmish/models/warrior.py` (99, 103, 107), `apps/common/domain/dice.py` (26),
`apps/common/validators.py` (10–13), `apps/faction/managers/faction.py` (12), plus a `__str__` on
half a dozen models.

### 4. Forms — and a defect to fix while you are there

`apps/account/forms/login.py` (33–35, 44→58, 47–49, 56) catches only `ObjectDoesNotExist` around
`User.objects.get(email=email)`. `User.email` has no uniqueness constraint, so two accounts sharing
an address raise an uncaught `MultipleObjectsReturned` and the login page answers 500.

`apps/warrior/forms/warrior.py:25` is the `RuntimeError` branch — now unreachable through the view,
which validates the attribute first, so test it directly on the form.

### 5. The remaining handler lines

The trivial mappers the strategy always ranked last. Largest cluster is
`apps/skirmish/handlers/events/battle_history.py` (10 one-line handlers). Then
`apps/quest/handlers/events/quest_contract.py` (16–22),
`apps/item/handlers/commands/item.py` (59–64), `apps/skirmish/handlers/commands/warrior.py`
(56–60, 146–148), and single lines across `month/`, `finance/`, `item/`, `training/`.

The registry tests already cover most of their risk — these are for the coverage gate.

### 6. Leftovers

- `apps/common/templatetags/utils.py:8` and `obsucrify.py` (9, 12). Note the typo in that filename;
  renaming it means touching every `{% load %}` that uses it.
- `apps/skirmish/management/commands/reset_skirmish.py` is at **0%** (18 statements). Decide whether
  to test it or omit management commands from coverage — it is a developer tool, not game code.

## What is expensive to rediscover

Things that cost time this round. None are obvious from the code.

**Strict mode blocks reads, not just writes.** `BlockDatabaseAccess` patches the cursor, so *any*
query inside an event handler fails — and `QUEUEBIE_STRICT_MODE = True` in `settings.py`, not only
in tests. A queryset passed into a message is fine, because it stays lazy until a command handler
consumes it; iterating or calling `.get()` on it is not. Both fatal bugs were this.

**Reference data comes from fixtures.** `Culture` and `ItemType` are loaded once per session by the
root `conftest.py`. Do not create them, and do not assume those tables are empty — a test that
asserted two drawn mercenaries shared a culture only passed while exactly one culture existed.

**`current_savegame` carries a `player_faction`** because three context processors dereference it on
every authenticated render. A bare savegame is not enough for anything that renders a template.

**The registry keys by string.** `command_dict` / `event_dict` are keyed by `message.module_path()`,
and the values are `{"module": ..., "name": ...}` dicts, not functions. Comparing classes against
those keys silently passes and tests nothing.

**Message equality works by value.** Messages are `@dataclass(kw_only=True)`, and the random `uuid`
lives on the non-dataclass `Message` base, so it is not a field. `assert result == SomeCommand(...)`
is safe. Handlers are keyword-only and return a bare message, a list, or `None`.

**`Transaction.for_savegame()` filters `faction__player_savegame`** — only the *player* faction's
money counts, not every faction in the savegame.

**A savegame has exactly one player.** Rival factions are NPCs, so a rival reading "another
faction's" data is not a leak. The pub belongs to the player, which is why
`handle_add_warrior_to_pub` targets `savegame.player_faction` deliberately.

**Tooling.** `boa-restrictor`'s PBR001 is exempted for `conftest.py` and `*/tests/*` because pytest
injects fixtures positionally. `ruff-format` rewrites files during pre-commit and fails the commit,
so expect one re-stage cycle — and check `git diff --cached` before committing, since a failed
hook leaves the index staged and unrelated files can ride along.

## How to verify a fix is real

Every fix in this branch was checked by reverting it and confirming exactly one test fails. Worth
keeping up: three of the smaller fixes had *no* coverage at first and the suite stayed green, which
proved nothing. Patch the source back, run the test, restore.
