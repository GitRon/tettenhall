# Month incidents

Between the player's own decisions, the world does something on its own. One incident is drawn per
month — most months draw nothing — and what it does reaches the game through the levers that already
exist. `apps/warband/incident/` owns the pool, the weights and the drawing; the effects belong to the apps
that own the rows.

## Adding one

An entry is a class in `apps/warband/incident/incidents/`, plus a line in the `INCIDENTS` tuple in that
package's `__init__.py`. Nothing else — a new entry does not touch the model, the log, or a handler:

```python
class TollOnTheOldRoad(Incident):
    WEIGHT = 3

    TITLE = "Traders paid to use the old road this month."
    BODY = "They asked what the toll bought them. They were told: the road."

    SILVER_CHANGE = 80
```

`Incident.resolve()` turns those constants into an `IncidentOutcome`. Override it only where the
outcome depends on the faction — which man the title names, which item goes missing, how much of a
reserve is actually left to lose — and override `is_possible()` where the entry needs something to
be there at all.

**Balance numbers live on the class**, the way a building's do in `apps/warband/town/buildings/`. The handler
reads them and hardcodes nothing.

**A magnitude is a constant, never a roll.** The variety is the pool's job. A rolled magnitude puts a
branch behind a dice throw, which the [coverage gate](coverage.md) rightly refuses, and hands a float
to a positive integer column, where anything below one truncates to nothing.

## The levers

| Lever | Field on the outcome | Command, and the handler that emits it |
|---|---|---|
| Silver | `silver_change` | `CreateTransaction` — `apps/warband/finance/handlers/events/incident.py` |
| Fyrd reserve | `fyrd_change` | `ChangeFyrdReserve` — `apps/warband/faction/handlers/events/incident.py` |
| Morale ceiling | `max_morale_share` + `warrior` | `ChangeWarriorMaxMorale` — `apps/warband/warrior/handlers/events/incident.py` |
| A piece of gear | `lost_item` | `LoseItem` — `apps/warband/item/handlers/events/incident.py` |

A lever left at its default is a lever the entry does not pull, and each of those four handlers
refuses an outcome that does not name its own.

The log line is not one of them: `title` and `body` have no default to leave alone, so
`handle_write_incident_to_month_log` in `apps/warband/month/handlers/events/incident.py` is the one reaction
every incident has, unguarded.

**The reactions live in the topic packages that own them**, not in
`apps/warband/incident/` — per [where code goes](app-layout.md), a handler belongs to the topic owning
the command it emits, in a module named after the topic the event came from. So
`apps/warband/incident/` chooses, and nothing there writes another topic's rows. A new lever costs a
field on the outcome and a handler in the owning topic; a new entry using the levers that exist costs a
class.

An entry that needs a lever this list has not got is not a baseline incident. It is a mechanic
wearing an incident's clothes, and it wants its own issue.

## The chain

```
PlayerMonthPrepared (evt)
  └─ handle_choose_incident_for_new_month → ChooseIncident (cmd)
       └─ handle_choose_incident            ← queries: which entries are possible, then draws one
            └─ IncidentOccurred (evt), carrying the resolved outcome
                 ├─ month:   handle_write_incident_to_month_log → CreatePlayerMonthLog
                 ├─ finance: handle_incident_silver             → CreateTransaction
                 ├─ faction: handle_incident_fyrd_reserve       → ChangeFyrdReserve
                 ├─ warrior: handle_incident_max_morale         → ChangeWarriorMaxMorale
                 └─ item:    handle_incident_lost_item          → LoseItem
```

**Drawing is a command handler because it has to ask questions** — does the treasury cover the
repair, is there a spare blade to lose — and [strict mode](strict-mode.md) blocks every database read
inside an event handler. Everything the outcome carries is therefore resolved before the event is
raised: the handlers reacting to it run behind the blocker.

**Registered on `PlayerMonthPrepared`, which is what keeps rivals out of the chronicle.** A rival has
no log to read it in. Moving that one handler to `FactionMonthPrepared` is what giving rivals
incidents would consist of, once #3 has given them an economy for one to mean anything.

## Questions

Most entries are notices: they happen, the effect lands, the player reads about it. An entry becomes a
question by declaring `OPTIONS` and naming one of them `DEFAULT_OPTION`:

```python
class AbbotAsksForLead(Incident):
    WEIGHT = 2

    TITLE = "The abbot of the minster asked for lead for the church roof."
    BODY = "He mentioned, in passing, how long the fyrd's mothers listen to him."

    OPTIONS = (
        IncidentOption(
            key="give", label="Give the lead", title="Lead went to the minster roof.", body="…", silver_change=-60
        ),
        IncidentOption(
            key="refuse",
            label="Refuse",
            title="The abbot was refused his lead, and preached on it.",
            body="…",
            fyrd_change=-1,
        ),
    )
    DEFAULT_OPTION = "refuse"
```

An option is the levers above with a button label and a chronicle line of its own. Answering turns it
into an ordinary `IncidentOutcome` and raises the same `IncidentOccurred`, so a question costs a class
like any other entry — no message, no view, no template. `IncidentOutcome.warrior` is there for a
question about a man, once one exists (#283).

```
ChooseIncident → handle_choose_incident
  └─ question drawn: PendingIncident row, IncidentAsked (evt, terminal)

PendingIncidentAnswerView (option key from POST, checked against OPTIONS, 400 otherwise)
  └─ AnswerPendingIncident → handle_answer_pending_incident → IncidentOccurred

PlayerMonthPrepared → handle_answer_open_pending_incidents_for_new_month
  └─ AnswerOpenPendingIncidents → handle_answer_open_pending_incidents → [IncidentOccurred]
```

- **Not answering is an answer.** A question still open when the month ends takes its default, dated to
  the new month so its line survives the log clearing. So ignoring a question never pays, and the month
  is never blocked by one.
- **A default never costs silver and never sells gear** — `test_pool.py` holds every entry to both. It
  is what a player who cannot afford anything else is left with, so a question can never wedge a
  savegame.
- **A question is priced by its dearest answer.** The inherited `is_possible` checks what the wages leave
  of the treasury against the most expensive option, so nobody is asked a question with a button he cannot press. The month
  goes on while it waits, so `get_pending_incident_answer_refusal` checks again when the answer is given.
- **Resolved when the answer lands.** `Incident.answer()` clamps a levy to what the reserve holds then.
  What the question was about — a rival, a piece of gear — is chosen by `ask()` and kept on the pending
  row, so the answer lands on the same one.
- **Balance counts a question at the answer that is not its default** — the one it was written to
  offer. Counting the default would price every question as if it were always ignored.
- **Shown as an attention card in the month log** with its options as buttons. A stopgap: #64 owns how a
  question finally looks.

## Two traps the hook comes with

**The player's month runs before any faction's.** `handle_prepare_month` returns
`PlayerMonthPrepared` ahead of every `FactionMonthPrepared`, and the bus drains FIFO, so
`is_possible()` sees the board the month opened with — before a warrior has been paid, healed or
rallied. Every entry today asks about something a month boundary does not change, which is what makes
that harmless. An entry that needs this month's state does not belong on this hook.

Silver is the one exception, and the base `is_possible` owns it. The salary run bills the same month
from the same opening balance, because no ledger row of the month — the incident's own included — lands
before every command has run. Weighed against the raw balance, a cost and the wages would each pass and
overdraw together. So a cost is weighed against `Payroll.remaining_amount`: the purse after the wages
the salary run will take, through the same projection it bills from. A month already short on wages
leaves nothing, so costly incidents fire less often in lean months. This month's building income is not
counted; it lands after the wages and funds the month after.

**Morale means the ceiling, not this month's morale.** `handle_replenish_warrior_morale` refills
every warrior to his maximum far later in the same month, so a change to `current_morale` made where
incidents are drawn is erased in the same tick. `max_morale` is the one morale number a month does not
touch — and it is close to a one-way ratchet, since nothing else raises it but a level-up, which is
why the entries moving it are weighted against each other.

## Months

An entry is drawn in every month unless it declares `MONTHS`, a tuple of month classes from
[the calendar](calendar.md). `handle_choose_incident` asks `is_drawn_in()` before `is_possible()`, so an
out-of-season entry never runs its queries.

**A month-bound entry carries a raised weight, so it is drawn as often across a year as before.**
`OathFeast` is a Yule feast, drawn only in Ærra Geola and Æfterra Geola at weight 18 — six times the 3
its balance against `PriestDenounces` and `ChildWithHisFace` is struck at, because it is in the pool two
months in twelve. `get_yearly_weight()` is that weight
averaged over the year, and it is what the pool's balance is measured in: the three drifts below net out
over a year, not inside any one month. Restricting an entry without raising its weight halves or worse
its share of the year, and silently breaks whatever it was weighted against.

## Weights

`QUIET_MONTH_WEIGHT` sits in `apps/warband/incident/incidents/__init__.py` beside the pool and stands in the
draw as the month where nothing happens. Two things follow: the odds of a quiet month are one number
somebody chose rather than a side effect of how many entries exist, and a month with nothing possible
is quiet for the same reason as any other month is.

It is deliberately larger than the pool's total weight in the busiest month of the year. The register
below works because most months are silent, and an incident every month is a chronicle nobody reads.

Per-entry weights price frequency; the constants price severity. Both matter, and `test_pool.py`
holds the three drifts that a reweighting is most likely to cause, each weighed at the yearly weight:

- **Silver nets out negative** across the pool. #45 gave insolvency teeth and #3 is about to make
  silver contested, so a pool that pays out on average flattens both.
- **The fyrd nets out flat.** The reserve is the brake on a war band's growth, so a drift here
  changes the pace of the whole game rather than one month of it.
- **The morale ceiling nets out flat**, because nothing corrects a permanent drift.

**Gear is the careful one.** It is the only lever that destroys something the player paid for, so it
carries the lowest weight in the pool *and* `losable_items()` keeps the finest weapon and the finest
armour in the field out of the draw. Losing a rusty spear is an anecdote; losing the sword the player
saved three months for is arbitrary, and no weight low enough makes that read as anything but the
game cheating.

## The register

The Anglo-Saxon Chronicle is the model: flat annalistic entries in one tonal key, where the humour
comes from what the chronicler thought worth recording rather than from anybody being funny. In
practice that is `TITLE` as one sentence of report and `BODY` as one sentence that quietly undercuts
it, with the narrator never commenting.

- **People are the joke, never the subject matter.** Vanity, greed, sloth, superstition and
  stubbornness are fair. Hunger, death, captivity and loss are not — `FeverInTheVillages` reports
  itself plainly for exactly that reason. No anachronism and no winking at the reader.
- **A funny entry still costs something.** Wighelm's sword has to be replaced, or the entry is a gag
  instead of an anecdote — and the effect is what makes it an incident rather than a line of text.
- **Dosage belongs with the weights.** No more than roughly one entry in three or four in the dry
  register, and never two in a month. The tone works because most entries are genuinely dry.

## See also

- [The message bus](message-bus.md) — why drawing is a command and applying is an event
- [Strict mode](strict-mode.md) — the database blocker that decides the shape above
- [Town buildings](town-buildings.md) — the same rule about where a balance number lives
