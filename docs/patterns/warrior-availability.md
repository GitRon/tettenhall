# Warrior availability

**A screen never drops a living man it will not let the player use. It draws him, greys him, and says
why — and the sentence it says comes out of the same place the exclusion does.**

Four rules decide whether a man can be sent anywhere this month. A picker that quietly filters on them
shows the player a shorter war band than the one he owns and leaves him to work out the difference,
which is the most expensive way for a rule to be communicated: it reads as a broken page.

## The one source

`apps/warband/warrior/services/availability.py` holds the rules, and `assess_roster()` is how a screen
asks:

```python
roster = assess_roster(faction_id=faction.id, month=month, excluded_ids=())
```

It hands back a `RosterAssessment` — the whole war band in draw order, each man carrying either a
reason or `None`. Everything a picker needs comes off that one object, so the rows a form renders and
the ids it validates can never be two answers to the same question:

| | |
|---|---|
| `as_queryset()` | every man, for the field's `queryset` |
| `reasons_by_warrior_id` | what the widget greys a row out with |
| `available_ids` | what a posted value is checked against |
| `is_empty` / `has_nobody_available` | a roster with no rows at all, versus one where every row is greyed. Different sentences |

## The dead are not on it

`assess_roster()` starts from `exclude_dead()`, so the rules below are only ever asked about men who
are still alive. Two reasons, and the first is the same one the whole pattern rests on:

- **Every other roster in the game leaves them out** — the faction page, the wage bill, the hand-out
  form, the incidents, the month standing. A picker that drew them would be *longer* than the war band
  it is meant to be counted against, which is the broken-page reading from the other direction.
- **A verdict is a prompt.** A wound heals, a fight can be settled, a month passes — each greyed row
  tells the player about something he can change. "Dead" tells him nothing he can act on, and it would
  tell him so for the rest of the savegame.

`filter_unfit()` on the queryset keeps its full meaning — it is the complement of `filter_healthy()`,
and narrowing it would move the rule away from the place that performs it. Inside the picker it simply
never meets a dead man.

## The rules

Held as one ordered tuple of `(query, reason)` pairs in `_blocking_rules()`. First match wins.

| Rule | The row reads |
|---|---|
| `filter_unfit()` | his condition — "Unconscious", "Fleeing" |
| `filter_sworn_to_a_quest(month=…)` | "Already sworn to a quest this month" |
| `filter_committed_to_a_fight(month=…)` | "Committed to a fight this month" |
| `filter_standing_in_an_open_fight()` | "Still standing in a fight nobody has settled" |

The queries are `WarriorQuerySet` methods, and `exclude_currently_busy()` is the exclusion of the last
three rather than a second spelling of them. **That is the whole point of the shape.** The sentence and
the query that performs it are one row, so a fifth rule is one more row instead of an edit in two
places — and a page cannot start saying one thing while the database does another.

Two orderings are deliberate:

- **Unfit is asked first**, because a man flat on his back is in no state to be spoken for.
- **"This month" is asked before "nobody settled it"**, which leaves the open-fight sentence to fire
  only for a fight from some *other* month. That is the one exclusion in this game a player cannot
  guess at — an unresolved skirmish carries over and goes on holding everyone on either roster — so it
  is worth a sentence of its own rather than being absorbed by the commoner case.

## What a picker has to do about it

A `<select multiple>` cannot do this: it has no room for a sentence per option and no portrait form
worth the name. Use `RosterCheckboxSelectMultiple` with the field template
`warrior/components/roster_picker_field.html`, wired through crispy per field:

```python
Field("assigned_warriors", template="warrior/components/roster_picker_field.html")
```

Per field, never as an override of the bootstrap5 pack — every other form in the project renders
against the stock one.

Two things follow, and the second bites silently:

- **The field's queryset holds the whole roster**, because an option that is not in it is an option
  that does not render.
- **So the queryset is no longer what validates the post.** `disabled` keeps the browser from
  submitting a greyed box and does nothing at all about a hand-edited one. Every form using the widget
  owns a `clean_<field>` that rejects anything outside `available_ids`. The queryset still scopes to
  the faction, and that part is load-bearing as ever.

Set the widget **before** the queryset. Assigning a queryset is what hands a field's choices to
whatever widget it is holding at that moment, so a widget swapped in afterwards renders nothing.

Colour follows [visual identity](visual-identity.md): the man's name goes `ink-dim` on a greyed row,
which is what that token is reserved for, but **the reason never does** — it is the one thing on the
row the player is there to read, and `ink-dim` may not carry meaning. It is `ink-muted`. Nothing here
is `blood`: a man being busy is not an error.

## See also

- [Warrior knowledge](warrior-knowledge.md) — the other rule every screen showing a man derives from
  rather than deciding again
- [Visual identity](visual-identity.md) — what a disabled row may be drawn in
