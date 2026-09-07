# Month incidents

Between the player's own decisions, the world does something on its own. One incident is drawn per
month — most months draw nothing — and what it does reaches the game through the levers that already
exist. `apps/incident/` owns the pool, the weights and the drawing; the effects belong to the apps
that own the rows.

## Adding one

An entry is a class in `apps/incident/incidents/`, plus a line in the `INCIDENTS` tuple in that
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

**Balance numbers live on the class**, the way a building's do in `apps/town/buildings/`. The handler
reads them and hardcodes nothing.

**A magnitude is a constant, never a roll.** The variety is the pool's job. A rolled magnitude puts a
branch behind a dice throw, which the [coverage gate](coverage.md) rightly refuses, and hands a float
to a positive integer column, where anything below one truncates to nothing.

## The levers

| Lever | Field on the outcome | Command it reaches |
|---|---|---|
| Silver | `silver_change` | `CreateTransaction` (`apps/finance`) |
| Fyrd reserve | `fyrd_change` | `ChangeFyrdReserve` (`apps/faction`) |
| Morale ceiling | `max_morale_share` + `warrior` | `ChangeWarriorMaxMorale` (`apps/warrior`) |
| A piece of gear | `lost_item` | `LoseItem` (`apps/item`) |

A lever left at its default is a lever the entry does not pull. Each has one event handler in
`apps/incident/handlers/events/incident.py` that refuses an outcome not naming its own — so a new
lever costs a field and a handler there, while a new entry using the existing ones costs a class.

An entry that needs a lever this list has not got is not a baseline incident. It is a mechanic
wearing an incident's clothes, and it wants its own issue.

## The chain

```
PlayerMonthPrepared (evt)
  └─ handle_choose_incident_for_new_month → ChooseIncident (cmd)
       └─ handle_choose_incident            ← queries: which entries are possible, then draws one
            └─ IncidentOccurred (evt), carrying the resolved outcome
                 ├─ handle_write_incident_to_month_log → CreatePlayerMonthLog
                 ├─ handle_incident_silver             → CreateTransaction
                 ├─ handle_incident_fyrd_reserve       → ChangeFyrdReserve
                 ├─ handle_incident_max_morale         → ChangeWarriorMaxMorale
                 └─ handle_incident_lost_item          → LoseItem
```

**Drawing is a command handler because it has to ask questions** — does the treasury cover the
repair, is there a spare blade to lose — and [strict mode](strict-mode.md) blocks every database read
inside an event handler. Everything the outcome carries is therefore resolved before the event is
raised: the handlers reacting to it run behind the blocker.

**Registered on `PlayerMonthPrepared`, which is what keeps rivals out of the chronicle.** A rival has
no log to read it in. Moving that one handler to `FactionMonthPrepared` is what giving rivals
incidents would consist of, once #3 has given them an economy for one to mean anything.

## Two traps the hook comes with

**The player's month runs before any faction's.** `handle_prepare_month` returns
`PlayerMonthPrepared` ahead of every `FactionMonthPrepared`, and the bus drains FIFO, so
`is_possible()` sees the board the month opened with — before a warrior has been paid, healed or
rallied. Every entry today asks about something a month boundary does not change, which is what makes
that harmless. An entry that needs this month's state does not belong on this hook.

**Morale means the ceiling, not this month's morale.** `handle_replenish_warrior_morale` refills
every warrior to his maximum far later in the same month, so a change to `current_morale` made where
incidents are drawn is erased in the same tick. `max_morale` is the one morale number a month does not
touch — and it is close to a one-way ratchet, since nothing else raises it but a level-up, which is
why the entries moving it are weighted against each other.

## Weights

`QUIET_MONTH_WEIGHT` sits in `apps/incident/incidents/__init__.py` beside the pool and stands in the
draw as the month where nothing happens. Two things follow: the odds of a quiet month are one number
somebody chose rather than a side effect of how many entries exist, and a month with nothing possible
is quiet for the same reason as any other month is.

It is deliberately larger than the pool's total weight. The register below works because most months
are silent, and an incident every month is a chronicle nobody reads.

Per-entry weights price frequency; the constants price severity. Both matter, and `test_pool.py`
holds the three drifts that a reweighting is most likely to cause:

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
