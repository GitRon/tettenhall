# Town buildings

Every faction owns exactly one `Town`, created together with the faction in `handle_create_new_faction`.
A town is created there rather than in reaction to `NewFactionCreated`, because several handlers of that
event already read `faction.town` and an event handler emitting a `CreateTown` command would land in the
same batch as those, with no guaranteed order.

The town stores only a **level** per building. `apps/warband/town/buildings/` turns a level back into the variant
holding that level's numbers:

- A **family** class names the building (`Hall`, `Weaponsmith`, `Marketplace`, `Sanctuary`) and lists its
  variants in `get_levels()`, ordered by level. It is a method rather than a class attribute because the
  variants are defined below the family class.
- `Building.get_building_by_type()` indexes that tuple, and `get_max_level()` is its last index — no
  building hardcodes how many levels it has.
- `BUILDINGS` in `apps/warband/town/buildings/__init__.py` maps the town field name to the family class. It is
  both the dispatch table and the whitelist for the upgrade URL; a building missing from it cannot be
  upgraded.
- `get_effects()` describes a level for the player, as `BuildingEffect(label, value)` pairs. It is
  implemented once per family and reads the variant's constants through `cls`, so a new level describes
  itself. **Every variant of a family has to answer with the same labels in the same order** — the upgrade
  page reads a level and the one above it side by side and zips the two `strict=True`. Where the two
  answer the same value, the page leaves that pair out rather than pricing a lever that is not moving,
  so **a level may lever only some of its family's effects**; at the maximum level there is no upgrade to
  describe and every pair is shown.

## Rules

- **Every number a building levers lives in `apps/warband/town/buildings/`** — the building costs and each
  building's effect. Don't hardcode a number in a handler that a building should own; the handler reads the
  constant. The upgrade page names the effects too, and reads them from the same place through
  `get_effects()`.
- **A balance number no building levers lives with the system that owns the mechanic**, as a class constant
  on that service or generator — `SkirmishDamageService.MINIMUM_DAMAGE_SHARE`, an item generator's
  `MODIFIER_ROLLS_MU`, a warrior generator's `STATS_MU`. `apps/warband/town/buildings/` is the home for levers, not
  a registry of every number in the game.
- **A number that differs per warrior or per item is a column, not a constant.** `Warrior.strength_baseline`
  is the archetype mean a man's strength is measured against, written by the generator that drew him: one
  constant on the attack service cannot sit on three archetype means at once.
- **Each building owns exactly one lever**: hall → monthly income + pub mercenary slots, weaponsmith →
  shop item quality, marketplace → resale ratio + shop stock size, sanctuary → monthly healing ceiling.
- **Level 0 is a baseline, not "no effect"**: a town without a hall still earns a little, and one without
  a market still holds three stalls. The `No…` class names describe the building, not the effect.
- **The hall pays in full only to the war band it asks for.** A level names its
  `WARRIORS_FOR_FULL_REVENUE` — the men on the payroll it needs, which is the mercenary slots it opens —
  and `get_revenue_for_war_band()` pays a share below that, floored at level 0's revenue. "On the payroll"
  is a living warrior drawing a wage, so the leader falls out by construction and a faction whose roster
  is its leader alone earns the baseline whatever it has built: the town is held by the men paid to hold
  it, and a hall bought in month one against no war band is not an annuity (#192). Every other building's
  lever is unconditional.
- **Costs escalate faster than effects** (roughly ×3.5 then ×2), so the top level of a building is
  deliberately a poor investment on its effect alone — the Large Hall is worth it for the third mercenary
  slot, not the revenue.
- **The first paid level is within the opening purse, and the step above it is the steepest in the game.**
  400–600 against the 1000 silver a faction starts with, so the first building leaves enough behind to pay
  a month's wages or hire a man; 1400–2100 for the second. The four families keep their order and their
  spread at every rung — marketplace cheapest, hall dearest — so the choice between them does not change
  as the town grows.
- **Only one building per month**, guarded by `Town.last_constructed_building_at`. Months count from
  1, so **0 means "nothing built yet"** — a town created with the current month in that field cannot
  build for the rest of it, which is why a new town leaves the field at its default.
- **The guard is enforced twice on purpose.** `get_building_upgrade_refusal`
  (`apps/warband/town/services/building_upgrade.py`) checks it to give the player a message, and
  `handle_upgrade_town_building` re-checks it as a single conditional `UPDATE ... WHERE`. Two
  overlapping requests both pass the first check, and the command handler returning `None` for the
  loser is what keeps the player from being charged twice. Don't turn that back into a
  read-modify-save.
- **The month guard is reported before the price**, which is why `get_building_upgrade_refusal` answers
  with the *first* refusal rather than collecting them. Both can apply to the same click, and the month is
  the one the player cannot do anything about until it is over — naming the price instead sends them off
  to raise silver they may not spend yet. The price is a disabled button on the page anyway, so a click
  reaching the view at all means the page was stale.
- **A rival's town is created at chosen levels, and stays there.** The player starts at every default;
  a rival is handed the sanctuary level named by `NPC_STARTING_SANCTUARY_LEVEL`
  (`apps/warband/town/buildings/sanctuary.py`), because the healing ceiling is the one lever that decides
  something for a faction the player never reaches into. Its other three buildings stay at 0 — their
  levers price or stock things only the player can use. The level is derived from `get_levels()` rather
  than written as a number, and `handle_heal_injured_warrior` keeps a single lookup for every faction, so
  nothing on the healing path knows what a rival is.
- **A faction without a town breaks four separate flows** (month advance, item sale, shop restock,
  warrior healing), all with `Town.DoesNotExist`. Anything that creates factions outside
  `handle_create_new_faction` — a data migration, a fixture, a management command — has to create the
  town too.

## Known gaps

- **NPC factions never build.** Nothing upgrades a rival's town, so every building effect is a
  player-only power curve. Construction proper is #68. The hall income is player-only to match: it hangs
  off `PlayerMonthPrepared`, the event for the things a rival has no equivalent of, and a rival earns off
  its war band instead (`apps/warband/faction/domain/rival_income.py`). A rival sits at `NoHall` for good,
  so the town would pay it a flat 50 silver however large its war band grew, against a leader's salary of
  around 135. The two incomes also count different rosters on purpose — the player's men on the payroll,
  a rival's men fit to march — and `RivalIncome` carries why.
- **Marketplace and sanctuary levels grant only their one lever each**, and the weaponsmith's quality
  bonus is the only thing making better gear — none of them has a second effect yet.
- **Item prices (~30–150 silver) are an order of magnitude below building costs**, so the marketplace's
  resale ratio is worth little in silver. Its stock size is the real draw, which is why it is priced below
  the other buildings.
- **The wage bill outweighs building costs early.** A warrior's salary is `round(recruitment_price * 0.5)`
  (`apps/warband/warrior/services/generators/warrior/base.py:173`), and what that comes to is the archetype's
  to decide — around 90 silver a month for a fyrd levy and 170 for a pub mercenary, priced against
  `PRICE_STATS_YARDSTICK` and `PRICE_HEALTH_YARDSTICK`. Each grows with `LEVEL_UP_GROWTH` alongside his
  attributes. The leader is the one man off the bill entirely: `draws_a_wage` is false on his generator,
  because he is bought by nobody, cannot be dismissed and cannot walk out, so a price on him would answer
  no decision the player ever makes. A faction opens with 1000 silver
  (`apps/warband/finance/handlers/events/faction.py:76`) and the cheapest upgrade in the game is the marketplace's
  first paid level at 400, so a band of four mercenaries bills more every month than that building costs
  once. Buildings are what the player saves for; wages are what stops him.
