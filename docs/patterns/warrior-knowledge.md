# What the player may know about a warrior

**A number the player has not earned is fuzzed. A thing he has not seen is absent.**

That is the whole rule, and it is normative for every screen that shows a man. Four screens used to
answer it separately, in three different ways, and three defects came out of the seams between them —
each one a screen that had been fixed a week apart from the screen one click away from it. Nothing was
wrong with any of the four answers; the rule they should all have been derived from was missing.

## The one question

**What does this warrior stand in relation to the viewer?** Three answers, and `WarriorKnowledge`
(`apps/warband/warrior/domain/knowledge.py`) is all three of them:

| Relation | Who | Numbers | Gear |
|---|---|---|---|
| `COMMANDED` | one of the player's own men | exact | named, and editable |
| `HELD` | a prisoner in his cells, a mercenary in his pub | **fuzzed** | named, not editable |
| `RIVAL` | somebody else's man, and anybody held by somebody else | **fuzzed** | **absent** |

- **Numbers** are strength, dexterity, health and morale.
- **Gear** is the weapon and the armor.
- **Everything else is public**, on every screen, for everybody: name, epithet, culture, faction,
  level, experience, salary, condition, town, leader, roster size. These are what a neighbour knows
  about a neighbour, and withholding them buys nothing.

A screen asks `knowledge.numbers_are_exact` and `knowledge.gear_is_visible`. It does not ask which
relation it is holding — asking that is how a fifth screen starts deciding for itself, which is the
thing this rule exists to stop.

## Why gear is the one omission

Fuzzing is the better of the two mechanisms and the rule uses it wherever it can: "their leader looks
strong" is information, and an empty row is not.

It does not reach gear, and the reason is mechanical rather than a matter of taste. The fuzz buckets a
value against the mean of what it was drawn with. A warrior's row carries its own means — `strength_baseline`,
`health_baseline`, `morale_baseline`, the columns `AttributeDraw` exists to read — and an item does not.
There is no honest average to call a seax high or low against, so gear is named or it is absent.

If a future change gives item types a comparable figure, gear joins the fuzz and this section goes away.

## Fuzz against the man's own baseline, never a literal

`obscurify` takes the value and the mean to judge it by. **The mean is always the warrior's own
baseline.** A fyrd levy and a mercenary are not drawn from the same distribution, and one number
standing for both calls the same strength high on one man and mediocre on the other.

Strength and dexterity share `strength_baseline` — they come out of one trio, which is why
`Warrior.attribute_draws` pairs them that way.

Two components render this, and a screen showing a number should use them rather than reaching for the
filter itself:

| Component | For |
|---|---|
| `warrior/components/warrior_attribute.html` | one attribute: `value`, `baseline`, `knowledge` |
| `warrior/components/warrior_gauge.html` | a current/maximum pair: `current`, `maximum`, `baseline`, `knowledge` |

The gauge's fuzzed form buckets where the man stands *now* against the ceiling a typical man of his kind
carries, so "Low" reads as somebody who has been hurt. Against his own maximum it would say nothing about
him at all: every unharmed warrior in the game would come out the same.

## Who answers the question

Never the template, and never per warrior in a loop.

- **`PlayerFactionAwareContextMixin`** (`apps/warband/faction/views.py`) answers `roster_knowledge` and
  `held_knowledge` for a faction's pages. A roster is that faction's own war band; a captive list and a
  pub are men it holds. The page and the htmx partials that replace parts of it all carry the mixin, so
  a swap cannot disagree with the page it swapped into — which is the defect that mixin already existed
  to prevent for the Sell button.
- **`WarriorDetailView`** answers `knowledge` off the memberships it already establishes for the roster
  navigation, through `WarriorKnowledge.for_relation()`.

Both the town square and the pub's own partial carry the mixin, because both are savegame-scoped: a
rival's faction id in the URL reaches a rival's pub, and men the player cannot hire are men he has not
been offered.

**This is a presentation rule and nothing else.** No queryset enforces it — a rival's warrior is
deliberately reachable by id, because a rival's page is a page the game means to serve. See
[savegame scoping](savegame-scoping.md) for the rule that *is* enforced, and note that the two are not
substitutes: scoping keeps one player out of another player's savegame, and this keeps one faction's
business off another faction's screen.

## The three screens this rule does not govern

Named here, because an unnamed exception is how the next seam opens.

- **The rivals list** (`faction/rival_faction_list.html`) renders factions, not men. Every column on it
  — name, culture, town, leader, roster size — is public by the rule above, including the warrior count.
- **The training progress table** (`training/components/warrior_progress_table.html`) is a screen about
  training the player's own men, and is omitted wholesale for a rival rather than fuzzed. A progress bar
  has no fuzzed form, and there is nothing on it he could act on for a man he does not command.
- **The fight screen** (`skirmish/warrior/components/warrior_card.html`) shows both sides' exact health,
  morale and gear, and that is deliberate: **a fight is scouting.** The player is standing across from
  the man, and a battle whose state he cannot read is not a battle he can make decisions in. Left
  ungated on purpose, which is the only thing separating it from an oversight.

## If a scouting action is ever added

This rule is what it unlocks, and nothing here blocks it: a scouted rival is a fourth relation, which is
one more enum member and one more row in the table above. The screens do not change, because they ask
the two properties rather than the relation.
