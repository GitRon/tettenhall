# Template components

**A template that is reused across pages is a component, not an include.** Components are
[django-cotton](https://github.com/wrabit/django-cotton): an HTML-like tag at the call site, a
template with its parameters declared at the top, and slots for markup the caller wraps.

```html
<c-common.svg-icon :icon_name="item.type.svg_image_name" size="xl" decorative />
<c-common.box-header>{{ faction.name }}</c-common.box-header>
<c-warrior.gauge :current="warrior.current_morale" :maximum="warrior.max_morale"
                 :peak="warrior.peak_max_morale" :baseline="warrior.morale_baseline" :knowledge="knowledge" />
```

An include has no contract: what it expects is only visible by reading it, and a misspelt parameter
renders as nothing. A component declares its parameters, and the tests below check every call site
against the declaration.

## Where a component lives

`<app>/templates/cotton/<topic>/<name>.html`, at the app root like every other template - see
[where code goes](app-layout.md). The tag is the path below `cotton/`: folders become dots and
underscores become hyphens, so `apps/warband/templates/cotton/warrior/gauge.html` is `<c-warrior.gauge>`.

**Always one topic folder.** Both apps share the one `cotton/` namespace, and the template loader takes
the first app that has the file, so a second `cotton/svg_icon.html` in another app is shadowed without a
word. The folder keeps the names apart, and the contract test fails on a name shipped twice.

| Component | Lives in | For |
|---|---|---|
| `<c-common.svg-icon>` | `apps.common` | A drawing from the hand-drawn icon set - see [visual identity](visual-identity.md#the-icons) |
| `<c-common.box-header>` | `apps.common` | A panel's heading, as the slot |
| `<c-common.card>` | `apps.common` | The card surface: the body as the slot, optional `header` and `footer` bands as named slots - see [visual identity](visual-identity.md#surface) |
| `<c-calendar.month-effects>` | `apps.warband` | One month's name, season and the effects it has in force, with an optional `heading` before the name |
| `<c-calendar.march-cost-row>` | `apps.warband` | The table row pricing a march in the month the form prices it with, on the attack page |
| `<c-faction.successor-line>` | `apps.warband` | Who takes the leader's seat if he falls, on the dashboard and the attack page; silent without a leader |
| `<c-finance.wage-bill-warning>` | `apps.warband` | The alert for a purse that cannot cover next month's wages, silent while it can; `show_finance_link` adds the way to the books |
| `<c-item.stats-meta>` | `apps.warband` | An item's roll and its average, the same in the shop, the stores and on the man; `show_price` adds the list price where it changes hands for it |
| `<c-item.improves-nobody-tag>` | `apps.warband` | The tag on an item every man already matches or beats in its slot |
| `<c-month.log-list>` | `apps.warband` | What one month's log puts to the player - attention and chronicle - with the open `questions` and their answers above it; a finished game passes no questions |
| `<c-month.log-brief>` | `apps.warband` | The rest of that month's log, read rather than acted on: the consequences and the tallied upkeep, silent when there are none |
| `<c-navigation.section-nav>` | `apps.warband` | The four sections of the game, `current` marked; a page whose section the url does not say passes its own - see [navigation](navigation.md) |
| `<c-skirmish.log-line>` | `apps.warband` | One line of a fight in either account; a casualty is set apart by whose loss it is (`casualty_side`) |
| `<c-skirmish.faction-box>` | `apps.warband` | One war band's panel on the fight screen, with its kit toggle and the roster that refreshes every round |
| `<c-skirmish.skirmish-table>` | `apps.warband` | A table of fights; `show_victor` adds the Victor column, and the row's control and the empty line are the caller's words |
| `<c-warrior.attribute>` | `apps.warband` | One attribute, exact or bucketed against his baseline - see [warrior knowledge](warrior-knowledge.md) |
| `<c-warrior.portrait>` | `apps.warband` | A man's stacked face, `card` or `full` crop, in the caller's `frame`; the silhouette when he has none - see [portraits](portraits.md) |
| `<c-warrior.portrait-layer>` | `apps.warband` | One beard or hair layer of the portrait, placed and tinted |
| `<c-warrior.row>` | `apps.warband` | One man as a row on a rival's roster, a rival's cells or a pub; `is_pub` adds the recruit control |
| `<c-warrior.roster-table>` | `apps.warband` | The table of the men the player decides about - his war band and his cells - with the rows as the slot |
| `<c-warrior.roster-row>` | `apps.warband` | One man as a line of that table, at the caller's `knowledge` and `wage`; the row menu is the slot, `unpaid_note` the line under his name |
| `<c-warrior.roster-gauge>` | `apps.warband` | A gauge in the roster and captive tables: the bar against his own maximum beside `<c-warrior.gauge>`, the word alone where the numbers are fuzzed |
| `<c-warrior.roster-gear>` | `apps.warband` | A weapon or armour cell in those tables, its roll and average under the name; a dash for an empty slot |
| `<c-warrior.gauge>` | `apps.warband` | A current/maximum pair, exact or fuzzed - see [warrior knowledge](warrior-knowledge.md) |

## Parameters

Declared in `<c-vars>` on the component's first line:

```html
<c-vars icon_name size="" decorative=False />
```

- **A name without a value is required.** Every call site has to pass it.
- **A name with a value is optional**, and the value is its default.
- **Every parameter is declared**, including the optional ones. A component sees its caller's context,
  the same as an include (see [context](#context)), so an undeclared name would quietly pick up whatever
  the caller has under it. A declared default shadows that.

At the call site, `:name="expression"` passes a value from the context, and `name="text"` passes the text.
A bare `name` passes `True`, which is how a flag reads: `<c-common.svg-icon icon_name="silver" decorative />`.

## Slots

Markup between the tags arrives as `{{ slot }}`. A component that wraps the caller's content - a box, a
card - takes it through the slot rather than through a parameter carrying markup. Named slots
(`<c-slot name="footer">`) are for a component with more than one place to fill.

## No logic in a component

A component places values; it does not compute them. A comparison, a threshold, a percentage or a choice
of icon goes into a template filter, a model property or a function next to the topic, with an ordinary
unit test there. `<c-warrior.gauge>` asks `maximum|is_below_peak:peak` rather than comparing in the
template.

## Context

Components run without context isolation. `COTTON_ENABLE_CONTEXT_ISOLATION` builds a fresh
`RequestContext` per render, which re-runs every context processor - the game's five, which read the
savegame, the balance and the roster, included - for every icon in every table row. Declaring every parameter is what makes sharing the context safe.

## Configuration

`apps/config/settings.py` installs `django_cotton.apps.SimpleAppConfig` and writes the loaders and the
builtin out explicitly. The default app config rewrites `TEMPLATES` in its `ready()`, so the settings
file would not say what runs. Both configs patch Django's template lexer so a template tag inside a
component attribute survives; that is private Django API, and the render test below is what notices a
Django upgrade breaking it.

## Tests

| Test | Holds |
|---|---|
| `apps/warband/tests/architecture/test_component_contracts.py` | Every tag names a component, every attribute passed is declared, every required one is passed, no name is shipped by two apps |
| `apps/warband/tests/architecture/test_component_render.py` | Every component renders with its required parameters, with all of them, and once per data branch, with an unresolved variable raising |
| Output tests next to the component's mirror path | What a component says and does - see [testing strategy](testing-strategy.md#components) |

A new component gets a row in the render test's table - the test fails until it has one - and an output
test per behaviour it has.

## See also

- [Testing strategy](testing-strategy.md#components) — what a component test may assert on
- [Architecture tests](architecture-tests.md)
