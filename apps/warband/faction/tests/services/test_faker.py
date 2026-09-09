from apps.faker_old_english import BYNAMES, OLD_ENGLISH_LOCALE
from apps.faker_old_english.data import GIVEN_NAMES
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

    assert result.first_name_male() in GIVEN_NAMES


def test_faker_for_locale_keeps_the_old_english_instance_single_locale():
    """
    "add_provider" raises in multiple locale mode, so the list this is built with has to stay one
    element long.
    """
    result = faker_for_locale(locale=OLD_ENGLISH_LOCALE)

    assert len(result.locales) == 1


def test_bynames_for_locale_hands_out_the_old_english_ones():
    result = bynames_for_locale(locale=OLD_ENGLISH_LOCALE)

    assert result == BYNAMES


def test_bynames_for_locale_has_none_for_another_culture():
    result = bynames_for_locale(locale="no_NO")

    assert result == ()
