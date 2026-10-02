# The calendar

A savegame counts months, and each of them is a named month of the Anglo-Saxon year. The year is Bede's
(*De temporum ratione*): twelve months, two seasons, no intercalary month. `apps/warband/calendar/` owns
the months, the seasons and the date; the rules that change with the month read it from there.

## Where a month's numbers live

Each month is a class in `apps/warband/calendar/months/`, in the style of the town's buildings:

- A **season class** — `Summer` in `summer.py`, `Winter` in `winter.py` — sets the numbers every month of
  it shares.
- A **month class** subclasses its season and overrides only what sets it apart. `Blotmonath` is a winter
  month with a cheaper march; `Winterfylleth` is a winter month and nothing more.
- `YEAR` in `months/__init__.py` lists the twelve in Bede's order, from Æfterra Geola to Ærra Geola.

A month's constants are the whole of what it does:

| Constant | Read by |
|---|---|
| `MARCH_COST_PER_WARRIOR` | the attack form (refusal), and the finance handler that pays a march |
| `TRAINING_FACTOR` | `handle_progress_warrior_training`, applied before the rounding and the floor at 1 |
| `HARVEST_SILVER` | the finance and month-log handlers on `FactionMonthPrepared` |
| `FYRD_REPLENISHES` | `handle_replenish_fyrd_reserve` |

**A number a month levers lives on the month or its season, never in a handler.** The handler asks
`get_calendar_month(month=...)` and reads the constant. `get_effects()` words the same constants for the
page, so the dashboard's description of a month and what the month does cannot drift apart. A new
constant needs a line in `get_effects()`, or the page stops telling the truth about it. A month that
levers nothing has no lines: the month band says nothing then, and the year strip says "Nothing out of
the ordinary." under a month that would otherwise open onto a bare title.

## Month, season and year

**The month of the year comes from `current_month` alone.** Month 1 is Eosturmonath, month 7 the first
Winterfylleth, and the year turns with Æfterra Geola in month 10. So every rule can ask it with the
`month` its message already carries, and none of them needs the savegame.

**The year needs `Savegame.start_year`**, drawn between AD 750 and AD 780 by the column's default when the
savegame is created. It carries no rule — nothing reads it but the display — so where in the range a game
opens cannot touch balance. `Savegame.current_date` turns the two into a `CalendarDate`, whose `label` is
the way a date is written everywhere: "Haligmonath · Summer · AD 768".

## Who the months reach

Everything the month does to a faction applies to every faction: the fyrd, training and the harvest hang
off `FactionMonthPrepared` or a per-faction command. The march cost is charged to whoever marches, which
today is only the player — rivals marching, and paying for it, is #315.

A march is a direct attack on a rival; a quest musters nobody and is not one. The attack form refuses a
march the purse cannot pay (`get_march_cost_refusal`, weighed against the balance as it stands, the way a
feast is), and the price is paid on `FactionWasAttacked`.

## Incidents

An incident may declare the months it can be drawn in — see [month incidents](month-incidents.md#months).

## Display

Months and seasons are labels, so they are set in `font-mono` wherever they are one — the resource bar,
the year at a glance, the march row on the attack page. The month band's heading stays a
heading, in the display face. See [visual identity](visual-identity.md).
