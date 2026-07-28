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

## Rules

- **Every game-balance number lives in `apps/town/buildings/`** — the building costs and each building's
  effect. Don't hardcode a number in a handler that a building should own; the handler reads the constant.
- **Each building owns exactly one lever**: hall → monthly income + pub mercenary slots, weaponsmith →
  shop item quality, marketplace → resale ratio + shop stock size, sanctuary → monthly healing ceiling.
- **Level 0 is a baseline, not "no effect"**: a town without a hall still earns a little, and one without
  a market still holds three stalls. The `No…` class names describe the building, not the effect.
- **Costs escalate faster than effects** (roughly ×2.3 then ×2), so the top level of a building is
  deliberately a poor investment on its effect alone — the Large Hall is worth it for the third mercenary
  slot, not the revenue.
- **Only one building per month**, guarded by `Town.last_constructed_building_at`.

## Known gaps

- **NPC factions never build.** `MonthPrepared` fans out to every faction and each one collects its hall
  income, but nothing upgrades a rival's town, so every building effect is a player-only power curve.
- **Marketplace and sanctuary levels grant only their one lever each**, and the weaponsmith's quality
  bonus is the only thing making better gear — none of them has a second effect yet.
- **Item prices (~30–150 silver) are an order of magnitude below building costs**, so the marketplace's
  resale ratio is worth little in silver. Its stock size is the real draw, which is why it is priced below
  the other buildings.
