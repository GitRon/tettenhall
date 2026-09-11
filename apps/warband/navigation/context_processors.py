from django.urls import reverse

from apps.warband.navigation.sections import SECTIONS, Page, Section, get_section_key
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


def _page_url(*, page: Page, player_faction_id: int | None) -> str:
    return reverse(page.url_name, args=[player_faction_id] if page.takes_player_faction else [])


def _section_url(*, section: Section, player_faction_id: int | None) -> str:
    return reverse(section.url_name, args=[player_faction_id] if section.takes_player_faction else [])


def navigation(request) -> dict:  # noqa: PBR001
    """
    The four sections, the pages of whichever one the player is standing in, and which of them to mark.

    Computed here rather than written out in "base.html" because two of the four entries are reversed
    with the player's own faction id, and a savegame can exist before its faction does - reversing
    either of those with an empty id raises, and the navbar is on every authenticated page.
    """
    current_savegame = get_current_savegame_for_request(request=request)
    # Before a savegame is loaded there is no month to lay out, and the only screens are the login
    # page and the savegame list, both of which carry their own way on.
    if not current_savegame:
        return {"nav_sections": [], "nav_pages": []}

    player_faction_id = current_savegame.player_faction_id
    # A page can be rendered with no url resolved behind it - the error handlers and
    # "render_to_string" both do it - and nothing is marked then.
    resolver_match = getattr(request, "resolver_match", None)
    current_section_key = get_section_key(
        url_name=resolver_match.url_name if resolver_match else None,
        url_kwargs=resolver_match.kwargs if resolver_match else None,
        player_faction_id=player_faction_id,
    )

    # An entry stays on the map whether or not there is anything behind it this month - the menu is a
    # map and not a to-do list. The one thing that does remove an entry is a savegame whose faction
    # has not been created yet, because its url cannot be built at all.
    sections = [
        {
            "key": section.key,
            "label": section.label,
            "icon": section.icon,
            "url": _section_url(section=section, player_faction_id=player_faction_id),
        }
        for section in SECTIONS
        if player_faction_id or not section.takes_player_faction
    ]

    current_section = next((section for section in SECTIONS if section.key == current_section_key), None)
    pages = (
        [
            {
                "label": page.label,
                "url": _page_url(page=page, player_faction_id=player_faction_id),
                "is_current": page.url_name == resolver_match.view_name,
            }
            for page in current_section.pages
            if player_faction_id or not page.takes_player_faction
        ]
        if current_section and resolver_match
        else []
    )

    return {
        "nav_sections": sections,
        "nav_pages": pages,
        "current_nav_section": current_section_key,
    }
