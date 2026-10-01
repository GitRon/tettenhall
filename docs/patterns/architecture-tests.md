# Architecture tests

`apps/warband/tests/architecture/` holds the tests that check the whole tree at once rather than one
testee. Each holds a rule that is otherwise silent when broken: the code keeps working, just wrongly, and
no unit test of a single function can see it. Every one that walks the Python tree finds its input through
`discovery.py`, see [registry tests](registry-tests.md).

An allowlist in one of them is part of the rule, not a way around it: every entry carries its reason, and
where an entry can go stale a test says so.

| Module | The rule it holds | Stated in |
|---|---|---|
| `test_registry.py` | The message wiring: eight rules over the queuebie registry | [Registry tests](registry-tests.md) |
| `test_view_scoping.py` | Every view resolving an object from the URL is scoped to the current player | [Savegame scoping](savegame-scoping.md#traps) |
| `test_ended_savegame_guard.py` | Every view dispatching a command refuses a decided savegame | [Savegame scoping](savegame-scoping.md#the-mixins) |
| `test_htmx_self_reloading_elements.py` | A self-reloading htmx element declares its swap, and one swapping `outerHTML` disinherits it | below |
| `test_item_pools.py` | Every item generator reaches a weapon and a piece of armour in the shipped reference data | below |
| `test_faker_construction.py` | A `Faker` is only built by the faction topic's factory | below |
| `test_record_managers.py` | A manager writes a record through `create_record()` | [Where code goes](app-layout.md#creating-a-record) |
| `test_admin_imports.py` | Every topic `admin.py` is imported by the app root's | [Where code goes](app-layout.md#the-app-root-is-djangos-everything-else-is-yours) |
| `test_component_contracts.py` | Every component call names a component, passes only what it declares and everything it requires | [Template components](components.md#tests) |
| `test_component_render.py` | Every component renders on every branch without an unresolved variable | [Template components](components.md#tests) |

## Self-reloading htmx elements

**An element carrying both `hx-get` and a `from:body` trigger declares its `hx-swap`.** It re-fetches
itself whenever another view fires that event, and whenever the view renders the template the element
lives in, the response contains the listening element itself. htmx's default swap is `innerHTML`, so the
reloaded copy lands *inside* the original and the page holds two listeners for one event — then four,
then eight. Nothing shows wrong data, since the last swap wins and is correct, so no status or context
assertion sees it and no player reports it. `outerHTML` is the answer for an element whose view renders
the element itself; `innerHTML` with an `hx-target` for one that only wraps a separate partial. Either is
a decision, the default is not.

**Such an element swapping `outerHTML` also sets `hx-disinherit="hx-swap"`.** `hx-swap` is inherited, so
without it a control inside that says nothing about its own swap replaces its target instead of filling
it — and on the second click the target is gone and the click does nothing.

The test scans the template sources, with Django tags and comments blanked first so a `>` inside one does
not end an element early.

## Item pools

**Every item generator — fyrd, leader and mercenary — reaches at least one weapon and one piece of armour
in the shipped reference data.** An empty pool is otherwise only discovered mid-savegame, as a
"No item type found." out of warrior generation. A tier renamed or dropped in the fixture fails here in CI.

## Faker construction

**`Faker(...)` is built in `apps.warband.faction.services.faker` and nowhere else.** Three of the five
cultures carry a locale Faker has never heard of — `ang`, `sga` and `ofs` for Old English, Old Irish and
Old Frisian — and their name stocks arrive through `Faker.add_provider()`, which only that factory knows to
do. `Faker([culture.locale])` written anywhere else raises for exactly those three cultures, and a test
reaching for a culture by `Culture.objects.first()` or a factory can just as easily get Norse and stay
green. So it is checked over the sources, for every construction site at once.
