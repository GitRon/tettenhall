# Savegame scoping

**A savegame has exactly one player.** Rival factions are NPCs, so a rival reading "another faction's"
data is not a leak. Every faction has a pub of its own, so `handle_add_warrior_to_pub` writes to the
`pub_owner` the message names rather than to `savegame.player_faction`, and the player hires only out of
his own - `RecruitPubMercenaryView` scopes to it. Money is the other case: every faction of a savegame keeps its
own purse, so `Transaction.for_faction()` and `Transaction.objects.current_balance()` take a faction id
rather than a savegame id, and the player-facing callers pass `savegame.player_faction_id`. Joining
`faction__player_savegame` would land on the player faction too — that is the reverse side of a
OneToOne — but would say "the faction owning this savegame" where "this faction" is meant.

Everything else that resolves an object has to be scoped, because the id comes straight from the URL.
This is the one view bug class that actually bites: everything else is a template detail, this one leaks
or changes another player's data.

## The mixins

`apps/warband/savegame/mixins.py` holds four. The two scoping ones narrow `super().get_queryset()`:

- **`SavegameScopedQuerysetMixin`** — restricts to the current savegame. The model's queryset must
  provide `for_savegame()`.
- **`PlayerFactionScopedQuerysetMixin`** — restricts to the current savegame's *player faction*. Stricter,
  and the right choice whenever the view acts on something the player owns: a savegame holds the player's
  faction plus its rivals, so scoping to the savegame still lets the URL reach a rival's objects. The
  model's queryset must provide `for_player_faction()`.

Both return `.none()` when there is no active savegame, so a view resolving a single object still has to
handle "nothing found" — see `PlayerTownMixin` in `apps/warband/town/views/town_upgrade.py`, which turns it into a
404 rather than dereferencing `None`.

The other two do not scope anything, but belong to the same question of which savegame a view acts on:

- **`RunningSavegameRequiredMixin`** — refuses a view once its savegame has been won or lost. **Every
  view dispatching a command carries it**, because a decided game must not change any more. An htmx
  request gets a 204 carrying the notice, a full-page navigation a message and a redirect to the
  dashboard. `SavegameCreateView` and `SavegameLoadView` deliberately go without: they are how a player
  leaves a finished savegame behind. `apps/warband/tests/architecture/test_ended_savegame_guard.py`
  checks every view calling `handle_message()` for it, with those two as its allowlist.
- **`CurrentSavegameMixin`** — puts the current savegame into the context. It inherits `ContextMixin`, so
  `super().get_context_data()` resolves on a plain `View` too.

## Traps

- **Never call `super().get_queryset()` from `get_object()`** when the scoping lives on the view class
  itself — that skips the override and returns everything. Go through `self.get_queryset()`.
- **`get_object_or_404()` with a bare model class** is unscoped by construction. Hand it a queryset.
- **A view carrying a scoping mixin that then queries a manager directly** has scoped nothing; the mixin
  becomes dead code.
- **Never build a URL parameter into `getattr`/`setattr`** on a model without checking it against a
  whitelist first, or the URL reaches any attribute of the object.

`apps/warband/tests/architecture/test_view_scoping.py` enforces the first three across every view at
once. The fourth is left to review. What the module checks, exactly:

- **Every view resolving an object from the URL scopes its queryset.** "Resolving from the URL" means
  carrying `SingleObjectMixin` or `MultipleObjectMixin`. "Scoped" is read off what the effective
  `get_queryset()` returns: every `return` has to go through one of `SCOPING_QUERYSET_METHODS`
  (`for_savegame`, `for_player_faction`, `in_pub_of`, `attackable_by`, …), end in `.none()`, or build on a
  `super().get_queryset()` that is scoped itself. An override returning `Model.objects.all()` fails.
- **No `get_object()` calls `super().get_queryset()`** — trap 1.
- **No `get_object_or_404()` / `get_list_or_404()` receives a bare model class** — trap 2.
- **A view carrying a scoping mixin reaches for a manager only in a statement that narrows it** — trap 3.
  That last one matches the statement's text, so a statement merely mentioning `current_savegame` passes.

Two lists carry the exceptions, each entry with its reason. `UNSCOPED_VIEWS` holds the views with nothing
to scope by: picking a savegame, logging in, a fragment resolving nothing. `UNCOLLECTED_SCOPED_VIEWS`
holds the views the check cannot see — a `TemplateView` or plain `View` querying scoped data itself —
and names the view test that plants another savegame's rows and asserts they stay out. A further test
fails when a view outside the collection is on neither list, and another when a view on the second list
grows a mixin that puts it back in reach of the real check.

## See also

- [Testing strategy](testing-strategy.md) — every view overriding `get_queryset()` needs its own scoping
  test
