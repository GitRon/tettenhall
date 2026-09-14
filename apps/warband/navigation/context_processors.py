from django.urls import reverse

from apps.warband.navigation.sections import SECTIONS, get_section_key
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


def navigation(request) -> dict:  # noqa: PBR001
    """
    The four sections, the pages of whichever one the player is standing in, and which of them to mark.

    Computed here rather than written out in "base.html" because two of the four mean nothing before
    the player has a faction, and a savegame can exist before its faction does - so the bar is not the
    same list on every page, and it is on every authenticated page.
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
    current_section_key = get_section_key(url_name=resolver_match.url_name if resolver_match else None)

    # An entry stays on the map whether or not there is anything behind it this month - the menu is a
    # map and not a to-do list. The one thing that does remove an entry is a savegame whose faction
    # has not been created yet, because the war band and the town are that faction's.
    sections = [
        {
            "key": section.key,
            "label": section.label,
            "icon": section.icon,
            "url": reverse(section.url_name),
        }
        for section in SECTIONS
        if player_faction_id or not section.needs_player_faction
    ]

    # Only among the entries that are actually on the bar. A savegame without a player faction has no
    # Town entry, and its page nav must not be offering Buildings under a section nothing names.
    rendered_keys = {section["key"] for section in sections}
    current_section = next(
        (section for section in SECTIONS if section.key == current_section_key and section.key in rendered_keys),
        None,
    )
    pages = (
        [
            {
                "label": page.label,
                "url": reverse(page.url_name),
                "is_current": page.url_name == resolver_match.view_name,
            }
            for page in current_section.pages
        ]
        if current_section and resolver_match
        else []
    )

    return {
        "nav_sections": sections,
        "nav_pages": pages,
        "current_nav_section": current_section_key,
    }
