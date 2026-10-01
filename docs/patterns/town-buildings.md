# Town buildings

Every faction owns exactly one `Town`, created together with the faction in `_create_faction`.
A town is created there rather than in reaction to `NewFactionCreated`, because several handlers of that
event already read `faction.town` and an event handler emitting a `CreateTown` command would land in the
same batch as those, with no guaranteed order.

The town stores only a **level** per building. `apps/warband/town/buildings/` turns a level back into the variant
holding that level's numbers:

- A **family** class names the building (`Hall`, `Weaponsmith`, `Marketplace`, `Sanctuary`,
  `Fortification`) and lists its
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

- **A changed balance number comes with a measurement.** Play a batch of seeded savegames before and after
  the change and compare them, see [measuring balance](measuring-balance.md).
- **Every number a building levers lives in `apps/warband/town/buildings/`** — the building costs and each
  building's effect. Don't hardcode a number in a handler that a building should own; the handler reads the
  constant. The upgrade page names the effects too, and reads them from the same place through
  `get_effects()`.
- **A balance number no building levers lives with the system that owns the mechanic**, as a class constant
  on that service or generator — `SkirmishDamageService.MINIMUM_DAMAGE_SHARE`, an item generator's
  `MODIFIER_ROLLS_MU`, a warrior generator's `STATS_MU`. `apps/warband/town/buildings/` is the home for levers, not
  a registry of every number in the game.
- **Which item types exist for whom is tuned in the `itemtype` fixture, through `tier`.** An item
  generator declares the bands it draws from (`BaseItemGenerator.item_tiers`) and the fixture decides which
  types sit in each, so moving a weapon between a levy's reach and a leader's is a data edit. That is a
  separate axis from the weaponsmith's `quality_bonus`, which sets an item's *quality* rather than which
  types a warrior can draw at all. No building levers the pool, so it does not live under
  `apps/warband/town/buildings/` despite the rule above.
- **A number that differs per warrior or per item is a column, not a constant.** `Warrior.strength_baseline`
  is the archetype mean a man's strength is measured against, written by the generator that drew him: one
  constant on the attack service cannot sit on three archetype means at once.
- **Each building owns exactly one lever**: hall → monthly income + pub mercenary slots + how much a feast mends + cell places, weaponsmith →
  shop item quality, marketplace → resale ratio + shop stock size, sanctuary → monthly healing ceiling, fortification →
  the `fortification_strength` a skirmish staged by a march on the town opens with (0 / 20 / 35 / 50). The
  fortification's defence bonus is not a lever: it is `SkirmishActionService.FORTIFICATION_DEFENSE_MULTIPLIER`,
  a constant of the mechanic.
- **Level 0 is a baseline, not "no effect"**: a town without a hall still earns a little, and one without
  a market still holds three stalls. The `No…` class names describe the building, not the effect.
  **The fortification is the one exception**: a town without a wall is fought in the open, so
  `NoFortification` stands at 0 and the attackers have no cover to break.
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
  a month's wages or hire a man; 1400–2100 for the second. The families keep their order and their
  spread at every rung — marketplace cheapest, weaponsmith, sanctuary and fortification level with each
  other, hall dearest — so the choice between them does not change
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
- **The war band feasts in the hall, once a month and all of it at once** (#173). A level's
  `FEAST_RESTORED_SHARE` is the share of a man's current morale ceiling a feast gives back, mended toward
  `Warrior.peak_max_morale` — the highest ceiling he has held — and never past it; `NoHall` stands at 0
  and cannot feast. The price is `FEAST_PRICE_PER_HEAD` times every living man under the banner, the
  leader and the unpaid included, because the whole roster eats: a man already at his mark is fed and
  charged and gains nothing, which is what keeps the feast a repair rather than nerve for sale.
  Captives have no banner and are not fed; an unpaid man is fed but not lifted
  (`Warrior.is_mended_by_a_feast`). `Town.last_feast_at` guards the month the way
  `last_constructed_building_at` guards building — asked by `get_feast_refusal`
  (`apps/warband/town/services/feast.py`) for the message, re-checked as a conditional `UPDATE` in
  `handle_throw_feast` so a double-click is charged once. The mending goes through
  `ChangeWarriorMaxMorale(restores_toward_peak=True)`: every other raise of the ceiling moves the mark
  along with it, every cut leaves the mark standing.
- **The cells are the hall's, and they are counted when the month turns** (#417). A level's `CELL_PLACES`
  (1 / 2 / 3 / 4) is how many prisoners the town still holds once the month has turned. A capture is never
  refused for want of room, so cells may stand over their places during a month; then
  `handle_let_captives_flee_overfull_cells`, off `FactionMonthPrepared`, lets exactly the excess go, picked
  at random from the held men ordered by id, so a seeded game replays. A fled man leaves the game the way an
  enslaved one does, without the silver. It is declared before the warriors' month, so a man who got away is
  not also healed by the sanctuary that held him. The cap limits the stock of trained men a war band sits
  on, not how many it takes in: men taken this month can all be recruited this month. `Town.get_cell_places`
  and `Faction.get_captives_over_cell_places` are the one count behind the flight, the Captives page and
  the Month page row, for every faction alike.
- **Every faction lives on its town.** The hall's revenue is the one income in the game, for the player
  and his rivals alike: `handle_earn_money_from_buildings` hangs off `FactionMonthPrepared`, and pays
  `Faction.get_monthly_income` for the men on the payroll. That is what makes a rival's strength
  readable off its town: its war band is as large as its hall carries.
- **A rival builds its hall the way the player does.** `RivalPolicy` weighs the next hall level as one
  more candidate in its month (the revenue it adds over `WAGE_HORIZON_MONTHS`, against its price), and
  raises it through the player's own `UpgradeTownBuilding`, offered only when
  `get_building_upgrade_refusal` has nothing against it. So the top level, the once-a-month rule and the
  price hold for a rival exactly as for the player. A rival starts with no hall and the 1000 silver the
  player starts with; in the harness every rival builds its Small Hall in month one.
- **A rival's other buildings are created at chosen levels, and stay there.** A rival is handed the
  sanctuary level named by `NPC_STARTING_SANCTUARY_LEVEL` (`apps/warband/town/buildings/sanctuary.py`)
  and the wall named by `NPC_STARTING_FORTIFICATION_LEVEL`, because the healing ceiling and the wall are
  the levers that decide something for a faction the player never reaches into. Its weaponsmith and
  marketplace stay at 0 — their levers price or stock things only the player can use. The levels are
  derived from `get_levels()` rather than written as numbers, and `handle_heal_injured_warrior` keeps a
  single lookup for every faction, so nothing on the healing path knows what a rival is.
- **A faction without a town breaks four separate flows** (month advance, item sale, shop restock,
  warrior healing), all with `Town.DoesNotExist`. Anything that creates factions outside
  `_create_faction` — a data migration, a fixture, a management command — has to create the
  town too.

## Known gaps

- **A rival builds only its hall.** The sanctuary, fortification, weaponsmith and marketplace ladders stay
  at their starting levels, so those effects are a player-only power curve - apart from the pub and the
  shop, which every faction restocks off its own hall, marketplace and weaponsmith. The other four ladders
  are #68.
- **Nobody reaches a second building level.** A rival spends everything above its wage bill every month,
  so its purse never holds the 1 400–2 100 a second level costs; the player is squeezed the same way. A
  rival's hall stops at the Small Hall, and the player's town at its first rungs. #416.
- **Marketplace and sanctuary levels grant only their one lever each**, and the weaponsmith's quality
  bonus is the only thing making better gear — none of them has a second effect yet.
- **Item prices (~30–150 silver) are an order of magnitude below building costs**, so the marketplace's
  resale ratio is worth little in silver. Its stock size is the real draw, which is why it is priced below
  the other buildings.
- **The wage bill outweighs building costs early.** A warrior's salary is his recruitment price times
  `Warrior.SALARY_SHARE_OF_PRICE` (0.5), never below `MINIMUM_MONTHLY_SALARY`
  (`Warrior.salary_for` in `apps/warband/skirmish/models/warrior.py`), and what that comes to is the archetype's
  to decide — around 80 silver a month for a fyrd levy and 160 for a pub mercenary, priced against
  `PRICE_STATS_YARDSTICK` and `PRICE_HEALTH_YARDSTICK`. Each grows with `LEVEL_UP_GROWTH` alongside his
  attributes. The leader is the one man off the bill entirely: `draws_a_wage` is false on his generator,
  because he is bought by nobody, cannot be dismissed and cannot walk out, so a price on him would answer
  no decision the player ever makes. A faction opens with 1000 silver
  (`STARTING_SILVER` in `apps/warband/finance/handlers/events/faction.py`) and the cheapest upgrade in the game is the marketplace's
  first paid level at 400, so a band of four mercenaries bills more every month than that building costs
  once. Buildings are what the player saves for; wages are what stops him.
