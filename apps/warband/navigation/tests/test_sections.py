from apps.warband.navigation.sections import get_section_key


def test_get_section_key_names_the_section_of_a_mapped_page():
    result = get_section_key(url_name="town-upgrade-view", url_kwargs={}, player_faction_id=1)

    assert result == "town"


def test_get_section_key_names_nothing_for_a_page_outside_the_map():
    """
    The ledger, the savegame screens and the login page are reachable without being anywhere on the
    map, and marking an entry on one of them would tell the player he is somewhere he is not.
    """
    result = get_section_key(url_name="transaction-list-view", url_kwargs={}, player_faction_id=1)

    assert result is None


def test_get_section_key_names_nothing_when_no_url_was_resolved():
    """
    The error handlers and "render_to_string" both render a page with no url behind it.
    """
    result = get_section_key(url_name=None, url_kwargs=None, player_faction_id=1)

    assert result is None


def test_get_section_key_reads_the_player_s_own_faction_page_as_the_war_band():
    """
    One view serves the player's own faction and a rival's alike, so the pk is the only thing that
    says which of the two sections the page is in.
    """
    result = get_section_key(url_name="faction-detail-view", url_kwargs={"pk": 7}, player_faction_id=7)

    assert result == "warband"


def test_get_section_key_reads_another_faction_page_as_a_rival():
    result = get_section_key(url_name="faction-detail-view", url_kwargs={"pk": 8}, player_faction_id=7)

    assert result == "rivals"


def test_get_section_key_names_nothing_for_a_faction_page_without_a_player_faction():
    """
    Nothing is the player's yet, so no faction page can be his own.
    """
    result = get_section_key(url_name="faction-detail-view", url_kwargs={"pk": 8}, player_faction_id=None)

    assert result is None
