# Town buildings

Every faction owns exactly one `Town`, created together with the faction in `handle_create_new_faction`.
A town is created there rather than in reaction to `NewFactionCreated`, because several handlers of that
event already read `faction.town` and an event handler emitting a `CreateTown` command would land in the
same batch as those, with no guaranteed order.

The town stores only a **level** per building. `apps/town/buildings/` turns a level back into the variant
holding that level's numbers:

- A **family** class names the building (`Hall`, `Weaponsmith`, `Marketplace`, `Sanctuary`) and lists its
  variants in `get_levels()`, ordered by level. It is a method rather than a class attribute because the
  variants are defined below the family class.
- `Building.get_building_by_type()` indexes that tuple, and `get_max_level()` is its last index — no
  building hardcodes how many levels it has.
- `BUILDINGS` in `apps/town/buildings/__init__.py` maps the town field name to the family class. It is
  both the dispatch table and the whitelist for the upgrade URL; a building missing from it cannot be
  upgraded.
- `get_effects()` describes a level for the player, as `BuildingEffect(label, value)` pairs. It is
  implemented once per family and reads the variant's constants through `cls`, so a new level describes
  itself. **Every variant of a family has to answer with the same labels in the same order** — the upgrade
  page reads a level and the one above it side by side and zips the two `strict=True`.

## Rules

- **Every number a building levers lives in `apps/town/buildings/`** — the building costs and each
  building's effect. Don't hardcode a number in a handler that a building should own; the handler reads the
  constant. The upgrade page names the effects too, and reads them from the same place through
  `get_effects()`.
- **A balance number no building levers lives with the system that owns the mechanic**, as a class constant
  on that service or generator — `SkirmishDamageService.MINIMUM_DAMAGE_SHARE`, an item generator's
  `MODIFIER_ROLLS_MU`, a warrior generator's `STATS_MU`. `apps/town/buildings/` is the home for levers, not
  a registry of every number in the game.
- **A number that differs per warrior or per item is a column, not a constant.** `Warrior.strength_baseline`
  is the archetype mean a man's strength is measured against, written by the generator that drew him: one
  constant on the attack service cannot sit on three archetype means at once.
- **Each building owns exactly one lever**: hall → monthly income + pub mercenary slots, weaponsmith →
  shop item quality, marketplace → resale ratio + shop stock size, sanctuary → monthly healing ceiling.
- **Level 0 is a baseline, not "no effect"**: a town without a hall still earns a little, and one without
  a market still holds three stalls. The `No…` class names describe the building, not the effect.
- **Costs escalate faster than effects** (roughly ×2.3 then ×2), so the top level of a building is
  deliberately a poor investment on its effect alone — the Large Hall is worth it for the third mercenary
  slot, not the revenue.
- **Only one building per month**, guarded by `Town.last_constructed_building_at`. Months count from
  1, so **0 means "nothing built yet"** — a town created with the current month in that field cannot
  build for the rest of it, which is why a new town leaves the field at its default.
- **The guard is enforced twice on purpose.** The view checks it to give the player a message, and
  `handle_upgrade_town_building` re-checks it as a single conditional `UPDATE ... WHERE`. Two
  overlapping requests both pass the view's check, and the command handler returning `None` for the
  loser is what keeps the player from being charged twice. Don't turn that back into a
  read-modify-save.
- **The month guard is reported before the price.** Both can apply to the same click, and the month is the
  one the player cannot do anything about until it is over — naming the price instead sends them off to
  raise silver they may not spend yet. The price is a disabled button on the page anyway, so a click
  reaching the view at all means the page was stale.
- **A rival's town is created at chosen levels, and stays there.** The player starts at every default;
  a rival is handed the sanctuary level named by `NPC_STARTING_SANCTUARY_LEVEL`
  (`apps/town/buildings/sanctuary.py`), because the healing ceiling is the one lever that decides
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
  its war band instead (`apps/faction/domain/rival_income.py`). Hall revenue is flat per level while a
  wage bill scales with the roster, so paying rivals through the town would move the constant and never
  the slope.
- **Marketplace and sanctuary levels grant only their one lever each**, and the weaponsmith's quality
  bonus is the only thing making better gear — none of them has a second effect yet.
- **Item prices (~30–150 silver) are an order of magnitude below building costs**, so the marketplace's
  resale ratio is worth little in silver. Its stock size is the real draw, which is why it is priced below
  the other buildings.
- **The wage bill outweighs building costs early.** A warrior's salary is `round(recruitment_price * 0.5)`
  (`apps/warrior/services/generators/warrior/base.py:126`), around 150 silver a month, and grows with
  `LEVEL_UP_GROWTH` alongside his attributes. A faction opens with 1000 silver
  (`apps/finance/handlers/events/faction.py:76`) and the cheapest upgrade in the game is the marketplace's
  first paid level at 600, so four men on the roster bill as much every month as that building costs once.
  Buildings are what the player saves for; wages are what stops him.
