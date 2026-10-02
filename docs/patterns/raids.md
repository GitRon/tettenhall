# Raids

**A march on a rival is one of three raids, and the raid decides the wall, what a victory takes and
whether the town falls. The fight itself is the same fight whichever it is.**

The kinds are a fixed set in code, in `apps/warband/skirmish/raids/`, the way the months are: a
`RaidKind` base class, one subclass per kind in `kinds.py`, `RAID_KINDS` in the order the attack page
offers them, and `get_raid_kind(value=...)` to read one back from the `RaidKindChoices` value stored on
`AttackFaction`, `FactionWasAttacked`, `CreateSkirmish` and `Skirmish.raid_kind`.

| Kind | Wall | A won raid takes, on top of the loot of the field | Opens the town |
|---|---|---|---|
| `LiftTheHerds` | none | a share of the rival's purse, capped (`PURSE_SHARE`, `PURSE_CAP`) | no |
| `BurnTheVillage` | none | names off the rival's fyrd reserve (`FYRD_NAMES_BURNED`) | no |
| `StormTheBurh` | the town's fortification | nothing more | yes |

The numbers are constants on the kind, under the rule in [town buildings](town-buildings.md) for a
balance number no building levers, and every change to one comes with a [measurement](measuring-balance.md).
`get_effects()` words them for the attack page, so the page and the raid read the same constants.

## Who defends

`get_raid_defenders` (`apps/warband/skirmish/services/raid_defenders.py`) is the one answer to who of a
rival's muster - every healthy man not already in a fight - stands in a raid's way. `handle_attack_faction`
asks it rather than mustering inline.

- **The burh** meets every man: they fall back behind the wall.
- **The herds and the village** meet only the men standing there. Each man of the muster is given one of
  the three places at random when the raid is staged, and if none landed where the raid falls, one of them
  is put there, so every raid is a fight and no side is ever empty.

The draw is a stand-in for a faction choosing where its men stand (#315), and the place locals who are not
in the war band join a defence (#398). It is drawn from the module-level `random`, over the muster in id
order, so a seeded game replays it.

## What a victory takes

`handle_take_raid_yield_after_victory`, on `SkirmishFinished`, sends `TakeRaidYield` when the attackers
won a raid that yields anything. Its handler reads the raided purse and reserve - the event handler may
not - clamps each yield to what there is, and emits `HerdsLifted` and `VillageBurned`. Those fan out to the
two ledger rows, `ChangeFyrdReserve`, a `SkirmishSpoil` of kind `KIND_HERDS_LIFTED` or
`KIND_VILLAGE_BURNED` for the fight report, and a battle log line. A raid spoil is taken off the faction
rather than off a man, so it carries no warrior.

## The town

`FactionQuerySet.occupiable_by` leaves out a rival in the month its band was beaten in a raid that does
not open the town. Finishing a rival is a choice made by storming the burh. It is an exclusion rather
than a demand for a won burh assault, so a rival left with nobody healthy for any other reason stays
occupiable and no rival can end up neither attackable nor occupiable.

## See also

- [Measuring balance](measuring-balance.md) — the `raider` policy
- [Town buildings](town-buildings.md) — the fortification, which only the burh meets
