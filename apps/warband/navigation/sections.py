"""
The top level of the game: four sections, and which page belongs to which.

The list here is the whole map a player has of the game, so it is one module rather than a set of
links spread through "base.html" - see docs/patterns/navigation.md for what each section owns and why
there are four of them.
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Page:
    """One page inside a section, for the sections that hold more than one."""

    label: str
    url_name: str
    # The faction-scoped urls take the player's own faction id. Reversing them without one raises,
    # which is what the guard in the context processor is for.
    takes_player_faction: bool = False


@dataclass(frozen=True, kw_only=True)
class Section:
    """One entry of the top level."""

    key: str
    label: str
    # Font Awesome, because the project's own icon set carries none of these four and a bar mixing
    # the two sets reads as two bars.
    icon: str
    url_name: str
    takes_player_faction: bool = False
    # Empty where the section is a single page. A second level is the price of a top level that fits
    # in a player's head, and only Town and Rivals pay it.
    pages: tuple[Page, ...] = ()


SECTIONS: tuple[Section, ...] = (
    Section(
        key="month",
        label="Month",
        icon="fa-calendar-days",
        url_name="warband:dashboard-view",
    ),
    Section(
        key="warband",
        label="Warband",
        icon="fa-users",
        url_name="warband:faction-detail-view",
        takes_player_faction=True,
    ),
    Section(
        key="town",
        label="Town",
        icon="fa-city",
        url_name="warband:town-square-view",
        takes_player_faction=True,
        pages=(
            Page(label="Town square", url_name="warband:town-square-view", takes_player_faction=True),
            Page(label="Buildings", url_name="warband:town-upgrade-view"),
        ),
    ),
    Section(
        key="rivals",
        label="Rivals",
        icon="fa-shield-halved",
        url_name="warband:rival-faction-list-view",
        pages=(
            Page(label="Rivals", url_name="warband:rival-faction-list-view"),
            Page(label="Skirmishes", url_name="warband:skirmish-list-view"),
        ),
    ),
)

# Every url name that renders a page a player can stand on, and the section it stands in. The action
# and htmx routes are deliberately absent: they answer a redirect or a fragment, so nothing is ever
# marked while one of them is running.
#
# "faction-detail-view" is missing on purpose - it serves the player's own faction and a rival's
# alike, so the pk decides, and "get_section_key" below is what asks. "warrior-detail-view" has the
# same shape and cannot be settled here at all: the url carries the man's id and not his faction's,
# so that page names its own section from its view.
SECTION_KEY_BY_URL_NAME: dict[str, str] = {
    "dashboard-view": "month",
    "training-edit-view": "month",
    "town-square-view": "town",
    "town-upgrade-view": "town",
    "quest-accept-view": "town",
    "rival-faction-list-view": "rivals",
    "faction-attack-view": "rivals",
    "skirmish-list-view": "rivals",
    "skirmish-fight-view": "rivals",
}


def get_section_key(*, url_name: str | None, url_kwargs: dict | None, player_faction_id: int | None) -> str | None:
    """
    Names the section the current page stands in, or None where no entry should be marked.

    None is a real answer and not a failure: the ledger, the savegame screens and the login page are
    reachable without being anywhere on the map, and marking an entry on one of them would tell the
    player he is somewhere he is not.
    """
    if url_name == "faction-detail-view":
        # The one page that serves two sections. Whose it is decides, and the pk is the only thing
        # that says so.
        if player_faction_id is None:
            return None
        return "warband" if (url_kwargs or {}).get("pk") == player_faction_id else "rivals"

    return SECTION_KEY_BY_URL_NAME.get(url_name)
