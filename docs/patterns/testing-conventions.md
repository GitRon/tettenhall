# Test conventions

The suite runs on **pytest** + **pytest-django** with **factory_boy** for test data. No
`unittest.TestCase` anywhere — plain test functions and plain `assert` throughout. No `setUpTestData`, no
`self.assertEqual`.

Already in place: `[tool.pytest.ini_options]` in `pyproject.toml` pointing at `apps.config.settings_test`,
and the `queuebie_registry` fixture in the root `conftest.py`, which resets the registry and its cache and
then autodiscovers. The registry is a process-wide singleton **and** is cached in Django's cache backend,
so without that reset registrations leak between tests.

## Layout

- Each app's `tests/` package mirrors the structure of its production code:
  `apps/item/services/generators/item.py` → `apps/item/tests/services/generators/test_item.py`.
- One test module per testee. If a module would have to hold tests for two testees, split it.
- **Always add `__init__.py`** to every `tests/` package and sub-package. Without it, two apps that both
  contain e.g. `tests/test_item.py` collide during collection and pytest fails on the duplicate module
  name.
- Order tests to reflect the order of functions and methods in the code under test.
- Group with plain functions. Use a `Test…` class only when several tests genuinely share fixtures, never
  just to namespace them.

## Naming

- `test_[testee]_[case]`, e.g. `test_handle_buy_item_for_faction_insufficient_silver`.
- Don't repeat the module name in the test name — it is already in the path.
- Avoid double underscores when testing protected functions.
- Use semantically useful names: `faction_with_two_warriors`, not `f1`.
- No type hints in variable names — avoid `warrior_qs`, `item_list`.

## Design

- Tests are atomic: one case per test. Avoid one large test covering every case.
- At least one test per function and one per branch — but don't overengineer, and one test per edge case,
  not more.
- Stick to **Arrange / Act / Assert**, separated by blank lines.
- Keep tests simple and readable: no loops, no clever abstractions, no helper indirection.
- Every test needs at least one assert. If the testee returns nothing and there is no other observable
  effect, assert `is None`.

## Assertions

- Use `pytest.raises(SomeError, match="expected message")` — never a bare `pytest.raises`, which also
  passes on the wrong error of the right type.
- Compare booleans identity-wise: `assert result is True` / `assert result is False`, not `assert result` —
  truthiness hides wrong types.
- Same for `None`: `assert result is None`.

## Imports

No local (function-level) imports in test files.
