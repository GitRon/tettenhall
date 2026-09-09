from apps.faker_gaelic import BYNAMES as GAELIC_BYNAMES
from apps.faker_gaelic import GAELIC_LOCALE
from apps.faker_gaelic.data import GIVEN_NAMES as GAELIC_GIVEN_NAMES
from apps.faker_old_english import BYNAMES as OLD_ENGLISH_BYNAMES
from apps.faker_old_english import OLD_ENGLISH_LOCALE
from apps.faker_old_english.data import GIVEN_NAMES as OLD_ENGLISH_GIVEN_NAMES
from apps.warband.faction.services.faker import bynames_for_locale, faker_for_locale


def test_faker_for_locale_falls_through_to_faker_itself():
    result = faker_for_locale(locale="no_NO")

    assert result.locales == ["no_NO"]


def test_faker_for_locale_names_an_old_english_warrior():
    """
    "ang" is a row in the culture table and not a Faker locale, so the instance stands on a base
    locale with the provider added on top.
    """
    result = faker_for_locale(locale=OLD_ENGLISH_LOCALE)

    assert result.first_name_male() in OLD_ENGLISH_GIVEN_NAMES


def test_faker_for_locale_names_a_gaelic_warrior():
    """
    And "sga" is the second such row, which the same table serves rather than a second factory.
    """
    result = faker_for_locale(locale=GAELIC_LOCALE)

    assert result.first_name_male() in [name.nominative for name in GAELIC_GIVEN_NAMES]


def test_faker_for_locale_builds_a_gaelic_instance_on_irish_english():
    """
    "en_IE" rather than "en_GB", so anything the game asks for beyond the two shadowed methods stays
    on the same island.
    """
    result = faker_for_locale(locale=GAELIC_LOCALE)

    assert result.locales == ["en_IE"]


def test_faker_for_locale_keeps_our_own_instances_single_locale():
    """
    "add_provider" raises in multiple locale mode, so the list either of them is built with has to
    stay one element long.
    """
    result = faker_for_locale(locale=OLD_ENGLISH_LOCALE)

    assert len(result.locales) == 1


def test_bynames_for_locale_hands_out_the_old_english_ones():
    result = bynames_for_locale(locale=OLD_ENGLISH_LOCALE)

    assert result == OLD_ENGLISH_BYNAMES


def test_bynames_for_locale_hands_out_the_gaelic_ones():
    result = bynames_for_locale(locale=GAELIC_LOCALE)

    assert result == GAELIC_BYNAMES


def test_bynames_for_locale_has_none_for_another_culture():
    result = bynames_for_locale(locale="no_NO")

    assert result == ()
