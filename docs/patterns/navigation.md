# Navigation

**The top level of the game is four sections, and it mirrors the month rather than the views.** Every
screen belongs to exactly one of them, and a new screen joins one of the four rather than becoming a
fifth. This is normative: a link added to the shell without a section is a link nobody can place.

## The four

| Section | Lands on | Answers | Also holds |
|---|---|---|---|
| **Month** | the dashboard | "What happened, and what do I still have to decide?" | the month log, the wage-bill warning, the active quests, the training choice |
| **Warband** | the roster | "Who do I have, and what shape are they in?" | the stores, the fyrd, the captives, the progress table, a warrior's page |
| **Town** | the board | "What can I turn silver into?" | the shop, the pub, the buildings, a quest's page |
| **Rivals** | the rivals list | "Who do I march on, and the fight itself" | a rival's page, the attack, the skirmish list, the fight |

The order is fixed and the entries never move. Four is the number a player holds in their head, and it
is also what makes a phone's bottom tab bar possible — the bar is the whole map, at every width.

`apps/warband/navigation/sections.py` is the list. It is one module and not a set of links in
`base.html`, because the bar is not the same list on every page and it is on every page.

**Two of the four entries mean nothing before the player has a faction**, and a section says so with
`needs_player_faction`. That is about having somewhere to go and not about reversing a url: every
entry on the map reverses without an id, because no page on it takes one.

## What is not a section

- **The ledger.** A scoreboard, not a place. It is one click from anywhere: the silver counter in the
  bar is a link to it, on every screen.
- **Finish month.** The one irreversible action in the game, and not navigation. It sits on the Month
  page itself, in the band that states whether the month can turn at all — the control and the
  sentence saying whether it may be pressed are one element, and an unresolved skirmish is what makes
  it refuse. The shell carries no control that ends the month, so there is exactly one place to press
  it and it is the section that owns the turn.
- **Savegames and Logout.** The account menu. They are about the session, not about the month.
- **The resource bar.** Global status. Each counter links to the page that answers it — the roster, the
  ledger, the open fights, the month — and the bar stays its own htmx swap target
  (`faction/components/resource_bar.html`).

## The second level

Three sections hold more than one page, and those three carry a page nav under the section nav:

| Section | Pages |
|---|---|
| **Warband** | Warband, Stores, Fyrd, Captives, Progress |
| **Town** | Board, Shop, Pub, Buildings |
| **Rivals** | Rivals, Skirmishes |

Month is one page and shows nothing. The landing page comes first because that is what the section
entry leads to; the rest are ordered by how often a month makes the player open them, which is why
Progress — a reference table nobody acts on — is last, and Buildings, which may be raised once a
month, is last under Town.

It comes off the current section's own page list, so a template never has to ask which section it is
in. There are no breadcrumbs: two levels do not need a third way of saying where the player is.

**The board is what the town lands on.** A quest decides who is spoken for and what the month is worth
spending on, so it is the offer the other three are weighed against: a sword bought before the board is
read is a sword bought against nothing. The stalls and the pub come after it because they answer a
question the board has already asked.

**No page carries a faction id.** Which faction is the player's is the savegame's answer, and
`PlayerFactionMixin` is what asks it — the same shape as `PlayerTownMixin`, which answers the same
question about his town. A url that took the id would be a url that could be pointed at a rival.
That is why the town's three lists are three pages rather than one screen reversed with his own id:
the pub, the shop and the board have nothing to say to each other, and the dashboard was already
offering them as three destinations.

## Marking where the player is

`apps/warband/navigation/context_processors.py` resolves the current section from the url name behind
the request and marks it with `aria-current="page"` plus a colour and a rule. The url name is the whole
answer — `SECTION_KEY_BY_URL_NAME` is a lookup and nothing else — with one exception:

- **A warrior's page** carries the man's id and not his faction's, so the section is not in the url at
  all. `WarriorDetailView` names its own (`nav_section`), and `warrior_detail.html` overrides the
  `navigation` block to pass it. His own men are Warband, a rival's are Rivals, a prisoner he holds is
  Warband and a mercenary in his pub is Town.

**A rival's page is the rivals' and nothing else.** `faction-detail-view` answers for a rival, and the
one id that is the player's own is redirected to the roster — so a bookmark, a fight report and the
counter in the bar all still land somewhere, and no url has to be told apart by whose id it carries.

A page that belongs to no section marks nothing, and that is a real answer rather than a failure: the
ledger, the savegame screens and the login page are all reachable without being anywhere on the map.

## The fight is a mode

`skirmish_fight.html` overrides the `navigation` block with nothing — both levels, because suppressing
only the sections would leave the page nav offering the same accidental way out. The fight carries its
own round loop and the month refuses to advance while it is unresolved, so it is not a destination to
be navigated away from by accident: it has one exit of its own, said before the fight and not only
after it.

## Rules

- **An entry stays visible when there is nothing behind it this month.** The menu is a stable map;
  "what is open to me right now" is the Month page's job. A menu that changed shape every month would
  be a worse map than none.
- **A label is a noun, never savegame data.** Two of the old seven entries read as a faction name and a
  town name, so a player looking for the pub had to know it lived behind the name of his own town.
- **An eighth destination becomes a page inside a section, not a fifth tab.** That is what four buys.
  Estates (#2) joins Town or Warband when it exists.
- **A page reachable from nowhere is a defect.** Every screen is either a section's landing page, a page
  on a section's page nav, or linked from a page that is.
- **A page is headed what the entry that leads to it says.** Month, Warband, Stores, Fyrd, Captives,
  Progress, Board, Shop, Pub, Buildings, Rivals, Skirmishes. A heading belongs to the page and never
  to a partial inside it: the shop's list and the pub's are htmx swap targets, so a heading in either
  is a heading the first purchase replaces. Every page of the game used to name itself
  differently from its own menu entry, so one wrong click was told apart from the right one by a
  heading worded differently from the link that produced it.

The labels are plain nouns. Whether the register becomes Old English — Fyrd, Burh — is #64's question;
the structure holds either way.

## Where the onward links are

Navigation is not only the shell. Three places create an intent the shell cannot serve:

- **A warrior's page** links back to the roster he was read off, and to the men either side of him in
  it. Without that, equipping a second man cost the same walk as the first.
- **A decided fight** links to the captives, because the prisoners it just made are there. A list of
  battles already fought is the one place its own report cannot be acted on.
- **The counters** link to what they count.

## See also

- [Responsive layout](responsive-layout.md) — the phone is the default, and the section nav is pinned to
  the bottom of it
- [Where code goes](app-layout.md) — why the templates sit at the app root
