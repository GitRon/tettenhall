# Savegame scoping

**A savegame has exactly one player.** Rival factions are NPCs, so a rival reading "another faction's"
data is not a leak. The pub belongs to the player, which is why `handle_add_warrior_to_pub` targets
`savegame.player_faction` deliberately. Money is the other case: every faction of a savegame keeps its
own purse, so `Transaction.for_faction()` and `Transaction.objects.current_balance()` take a faction id
rather than a savegame id, and the player-facing callers pass `savegame.player_faction_id`.

Everything else that resolves an object has to be scoped, because the id comes straight from the URL.
This is the one view bug class that actually bites: everything else is a template detail, this one leaks
or changes another player's data.

## The two mixins

Both live in `apps/savegame/mixins.py` and narrow `super().get_queryset()`:

- **`SavegameScopedQuerysetMixin`** — restricts to the current savegame. The model's queryset must
  provide `for_savegame()`.
- **`PlayerFactionScopedQuerysetMixin`** — restricts to the current savegame's *player faction*. Stricter,
  and the right choice whenever the view acts on something the player owns: a savegame holds the player's
  faction plus its rivals, so scoping to the savegame still lets the URL reach a rival's objects. The
  model's queryset must provide `for_player_faction()`.

Both return `.none()` when there is no active savegame, so a view resolving a single object still has to
handle "nothing found" — see `PlayerTownMixin` in `apps/town/views/town_upgrade.py`, which turns it into a
404 rather than dereferencing `None`.

## Traps

- **Never call `super().get_queryset()` from `get_object()`** when the scoping lives on the view class
  itself — that skips the override and returns everything. Go through `self.get_queryset()`.
- **`get_object_or_404()` with a bare model class** is unscoped by construction. Hand it a queryset.
- **A view carrying a scoping mixin that then queries a manager directly** has scoped nothing; the mixin
  becomes dead code.
- **Never build a URL parameter into `getattr`/`setattr`** on a model without checking it against a
  whitelist first, or the URL reaches any attribute of the object.

`apps/common/tests/test_view_scoping.py` enforces the first three across every view at once, and carries
`UNSCOPED_VIEWS` for the deliberate exceptions — each entry needs a reason.

## See also

- [Testing strategy](testing-strategy.md) — every view overriding `get_queryset()` needs its own scoping
  test
