from unittest import mock

from faker import Faker
from faker.generator import Generator

from apps.faker_gaelic.data import FEMININE, GIVEN_NAMES, MASCULINE, GivenName, PlaceGeneric
from apps.faker_gaelic.provider import GaelicProvider, compose, lenite

CILL = PlaceGeneric("Cill", FEMININE)
DUN = PlaceGeneric("Dún", MASCULINE)
RATH = PlaceGeneric("Ráth", FEMININE)


def test_lenite_writes_an_h_after_the_initial():
    """
    "Cill Chiaráin" - the church of Ciarán, and the commonest shape an Irish place name has.
    """
    result = lenite(word="Ciaráin", preceding="Cill")

    assert result == "Chiaráin"


def test_lenite_leaves_a_vowel_alone():
    result = lenite(word="Áeda", preceding="Cill")

    assert result == "Áeda"


def test_lenite_leaves_an_unlenitable_consonant_alone():
    """
    "l", "n" and "r" take no lenition, so the church of Lorcán is "Cill Lorcáin".
    """
    result = lenite(word="Lorcáin", preceding="Cill")

    assert result == "Lorcáin"


def test_lenite_leaves_an_s_before_a_stop_alone():
    result = lenite(word="Scandláin", preceding="Ráth")

    assert result == "Scandláin"


def test_lenite_writes_an_s_before_anything_else():
    result = lenite(word="Sailech", preceding="Ráth")

    assert result == "Shailech"


def test_lenite_leaves_a_dental_after_a_dental_alone():
    """
    The dentals rule, and the reason the church of the oak is "Cill Dara" rather than "Cill Dhara".
    """
    result = lenite(word="Dara", preceding="Cill")

    assert result == "Dara"


def test_lenite_writes_a_dental_after_anything_else():
    result = lenite(word="Domnaill", preceding="Ráth")

    assert result == "Dhomnaill"


def test_compose_lenites_after_a_feminine_generic():
    result = compose(generic=CILL, qualifier="Cormaic")

    assert result == "Cill Chormaic"


def test_compose_leaves_a_masculine_generic_alone():
    result = compose(generic=DUN, qualifier="Cormaic")

    assert result == "Dún Cormaic"


def test_first_name_male_is_drawn_from_the_pool():
    provider = GaelicProvider(Generator())

    result = provider.first_name_male()

    assert result in [name.nominative for name in GIVEN_NAMES]


def test_provider_draws_with_weighting():
    """
    Faker only sets this while building a factory of its own, so a provider handed in through
    "add_provider" carries the class default - and with weighting off the weights on the place-name
    patterns are read, discarded and replaced by a uniform draw, with nothing to see from the outside.
    """
    result = GaelicProvider.__use_weighting__

    assert result is True


def test_city_composes_the_pattern_it_drew():
    """
    The first draw picks the pattern, the rest of them fill it in.
    """
    provider = GaelicProvider(Generator())

    with mock.patch.object(
        provider, "random_element", side_effect=[provider._possessive_place, DUN, GivenName("Cormac", "Cormaic")]
    ):
        result = provider.city()

    assert result == "Dún Cormaic"


def test_possessive_place_names_the_man_who_holds_it():
    provider = GaelicProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=[CILL, GivenName("Ciarán", "Ciaráin")]):
        result = provider._possessive_place()

    assert result == "Cill Chiaráin"


def test_feature_place_names_what_the_land_holds():
    provider = GaelicProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=[CILL, "Dara"]):
        result = provider._feature_place()

    assert result == "Cill Dara"


def test_qualified_place_names_a_quality():
    provider = GaelicProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=[RATH, "Mór"]):
        result = provider._qualified_place()

    assert result == "Ráth Mhór"


def test_provider_draws_reproduce_under_a_seed():
    """
    Every draw goes through "random_element" rather than the "random" module, which is what makes a
    seeded run repeatable. Seeded per instance rather than through "Faker.seed", because that one is
    process-global and would follow the rest of the session around.
    """
    first = Faker(["en_IE"])
    first.add_provider(GaelicProvider)
    first.seed_instance(4711)
    second = Faker(["en_IE"])
    second.add_provider(GaelicProvider)
    second.seed_instance(4711)

    result = [first.first_name_male(), first.city()]

    assert result == [second.first_name_male(), second.city()]
