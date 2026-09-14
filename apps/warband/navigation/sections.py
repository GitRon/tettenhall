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


@dataclass(frozen=True, kw_only=True)
class Section:
    """One entry of the top level."""

    key: str
    label: str
    # Font Awesome, because the project's own icon set carries none of these four and a bar mixing
    # the two sets reads as two bars.
    icon: str
    url_name: str
    # Whether the entry means anything before the player has a faction. Every url on the map reverses
    # without one - the war band's pages and the town's alike read the faction off the savegame
    # rather than out of the url - so this is about having somewhere to go, not about reversing.
    needs_player_faction: bool = False
    # Empty where the section is a single page. A second level is the price of a top level that fits
    # in a player's head, and three of the four pay it.
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
        url_name="warband:warband-roster-view",
        needs_player_faction=True,
        pages=(
            Page(label="Warband", url_name="warband:warband-roster-view"),
            Page(label="Stores", url_name="warband:warband-stores-view"),
            Page(label="Fyrd", url_name="warband:warband-fyrd-view"),
            Page(label="Captives", url_name="warband:warband-captives-view"),
            Page(label="Progress", url_name="warband:warband-progress-view"),
        ),
    ),
    Section(
        key="town",
        label="Town",
        icon="fa-city",
        url_name="warband:town-board-view",
        needs_player_faction=True,
        pages=(
            Page(label="Board", url_name="warband:town-board-view"),
            Page(label="Shop", url_name="warband:town-shop-view"),
            Page(label="Pub", url_name="warband:town-pub-view"),
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
# "warrior-detail-view" is missing on purpose and cannot be settled here at all: the url carries the
# man's id and not his faction's, so that page names its own section from its view.
SECTION_KEY_BY_URL_NAME: dict[str, str] = {
    "dashboard-view": "month",
    "training-edit-view": "month",
    "warband-roster-view": "warband",
    "warband-stores-view": "warband",
    "warband-fyrd-view": "warband",
    "warband-captives-view": "warband",
    "warband-progress-view": "warband",
    "town-shop-view": "town",
    "town-pub-view": "town",
    "town-board-view": "town",
    "town-upgrade-view": "town",
    "quest-accept-view": "town",
    "rival-faction-list-view": "rivals",
    "faction-detail-view": "rivals",
    "faction-attack-view": "rivals",
    "skirmish-list-view": "rivals",
    "skirmish-fight-view": "rivals",
}


def get_section_key(*, url_name: str | None) -> str | None:
    """
    Names the section the current page stands in, or None where no entry should be marked.

    None is a real answer and not a failure: the ledger, the savegame screens and the login page are
    reachable without being anywhere on the map, and marking an entry on one of them would tell the
    player he is somewhere he is not.
    """
    return SECTION_KEY_BY_URL_NAME.get(url_name)
