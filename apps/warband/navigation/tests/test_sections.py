from apps.warband.navigation.sections import get_section_key


def test_get_section_key_names_the_section_of_a_mapped_page():
    result = get_section_key(url_name="town-upgrade-view")

    assert result == "town"


def test_get_section_key_names_nothing_for_a_page_outside_the_map():
    """
    The ledger, the savegame screens and the login page are reachable without being anywhere on the
    map, and marking an entry on one of them would tell the player he is somewhere he is not.
    """
    result = get_section_key(url_name="transaction-list-view")

    assert result is None


def test_get_section_key_names_nothing_when_no_url_was_resolved():
    """
    The error handlers and "render_to_string" both render a page with no url behind it.
    """
    result = get_section_key(url_name=None)

    assert result is None


def test_get_section_key_reads_a_faction_page_as_a_rival():
    """
    The player's own war band is five pages of its own, so a faction page is a rival's whoever the
    id belongs to - and the one id that is his own never renders, it redirects.
    """
    result = get_section_key(url_name="faction-detail-view")

    assert result == "rivals"


def test_get_section_key_reads_the_war_band_pages_as_the_war_band():
    assert get_section_key(url_name="warband-roster-view") == "warband"
    assert get_section_key(url_name="warband-progress-view") == "warband"
