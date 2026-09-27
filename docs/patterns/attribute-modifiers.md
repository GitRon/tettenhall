# Attribute modifiers

**A thing that makes a warrior weaker or quicker is a modifier read at the point of use, never a
subtraction from the stored column.**

Two columns already write `strength` and `dexterity` — `apply_level_up_growth` and the training
handler — so a source that wrote to them as well would collide with both: a crippled man who levels
silently un-cripples, and nothing could tell an injury from a bad roll at generation. The stored value
stays the man as he was made and as his career has grown him; what he brings to the field today is
derived.

## The seam

Two properties on `Warrior`, and every reader points at one of them:

| Property | Read by |
|---|---|
| `effective_strength` | `SkirmishActionService._scaled_by_strength`, `Warrior.expected_damage`, `SkirmishActionDecisionService` |
| `effective_dexterity` | both `get_pair_matching_points` call sites in `handle_determine_attacker_and_defender`, `SkirmishActionDecisionService` |

**Per attribute, not per call site.** A seam built only into the attack service would miss dexterity
entirely — it never goes through one. The three attack services reach `_scaled_by_strength` with an
`action_multiplier` rather than repeating the formula, which is what makes that one method the whole of
strength's side.

`MINIMUM_EFFECTIVE_ATTRIBUTE` floors both at a point. Strength scales a blow by
`strength / strength_baseline`, so a zero is a man who can never hurt anybody again — a worse outcome
than the death he was one point short of, and reachable by no other route.

## What does not read the seam

- **`Warrior.attribute_draws`**, which feeds the epithet. A nickname is drawn once and kept, so nothing
  that moves an attribute afterwards may rename a man — not a level, not a training course, and not an
  injury. *The Strong* who loses a shoulder is still *the Strong*.
- **The cards**, which print the stored figure and list what a man carries beside it. The fuzz in
  `warrior/components/warrior_attribute.html` buckets a value against the distribution it was drawn
  from ([warrior knowledge](warrior-knowledge.md)), and feeding it a modified value would change what
  "High" means rather than telling the player anything. What they list beside it is the injuries only: no
  screen renders a trait, which the player finds out through the fights it changes.

## The sources

Each source owns its own reference table; they share only the layer above.

| Source | Table | Status |
|---|---|---|
| Permanent injuries | `InjuryType`, fixture-backed | shipped |
| Innate and earned traits | `TraitType`, fixture-backed | shipped |
| Item bonuses and drawbacks | `ItemType` | #23 |

**Do not merge the catalogues.** An injury entry is a name, an attribute and a magnitude; a trait needs
all of that plus an exclusive-group key, a sign, a source and the hook an incident pool selects on — so
one table would carry a kind discriminator and a column set that is dead for half the rows. Visibility
is the clearest case: an injury is shown on every card and a trait is hidden until the man shows you
one, which is one column with opposite constant values per kind.

A source is one aggregation on `Warrior` — `injury_maluses`, `trait_modifiers` — summed per attribute in
one query and cached on the instance, and `_effective_attribute` adds them up. A new source is a third
such property and a term in that sum, and nothing else. Two sources on one attribute simply sum, which is
why the floor above sits on the result rather than on any one source: a slight man with a ruined
shoulder is floored once. The attribute keys are `ModifiedAttributeChoices`, one set every source's
catalogue uses, so the sum has one vocabulary.

## See also

- [Town buildings](town-buildings.md) — where a balance number lives when no building levers it
- [Warrior knowledge](warrior-knowledge.md) — why the cards print the stored figure
- [Where code goes](app-layout.md) — the `warrior` topic package, which owns the injury and trait models
