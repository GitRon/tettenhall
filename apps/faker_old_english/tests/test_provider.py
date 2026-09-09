from unittest import mock

from faker import Faker
from faker.generator import Generator

from apps.faker_old_english.data import GIVEN_NAMES
from apps.faker_old_english.provider import OldEnglishProvider, compound, folk_stem, genitive


def test_folk_stem_loses_a_final_vowel():
    """
    "Offa" gives "Offinga-", not "Offainga-".
    """
    result = folk_stem(name="Offa")

    assert result == "Off"


def test_folk_stem_keeps_a_final_consonant():
    result = folk_stem(name="Wulfstan")

    assert result == "Wulfstan"


def test_genitive_of_a_weak_name_takes_an():
    """
    "Dudda" is a weak noun, so the genitive is "Duddan-" and the place is "Duddanham".
    """
    result = genitive(name="Dudda")

    assert result == "Duddan"


def test_genitive_of_a_strong_name_takes_es():
    result = genitive(name="Wulfstan")

    assert result == "Wulfstanes"


def test_genitive_absorbs_a_final_e():
    """
    "Deorwine" is "Deorwines-", not "Deorwinees-", and the "-wine" names are a good tenth of the pool.
    """
    result = genitive(name="Deorwine")

    assert result == "Deorwines"


def test_compound_writes_a_doubled_consonant_once():
    """
    "Aesc" and "ceaster" make "Aesceaster" - the seam carries one "c", the way it is said.
    """
    result = compound(stem="Aesc", generic="ceaster")

    assert result == "Aesceaster"


def test_compound_joins_a_stem_and_a_generic():
    result = compound(stem="Stan", generic="tun")

    assert result == "Stantun"


def test_first_name_male_is_drawn_from_the_pool():
    provider = OldEnglishProvider(Generator())

    result = provider.first_name_male()

    assert result in GIVEN_NAMES


def test_provider_draws_with_weighting():
    """
    Faker only sets this while building a factory of its own, so a provider handed in through
    "add_provider" carries the class default - and with weighting off the weights on the place-name
    patterns are read, discarded and replaced by a uniform draw, with nothing to see from the outside.
    """
    result = OldEnglishProvider.__use_weighting__

    assert result is True


def test_city_composes_the_pattern_it_drew():
    """
    The first draw picks the pattern, the rest of them fill it in.
    """
    provider = OldEnglishProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=[provider._descriptive_place, "Stan", "tun"]):
        result = provider.city()

    assert result == "Stantun"


def test_descriptive_place_names_the_land():
    provider = OldEnglishProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Broc", "ham"]):
        result = provider._descriptive_place()

    assert result == "Brocham"


def test_folk_place_names_the_group_descended_from_a_man():
    provider = OldEnglishProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Offa", "tun"]):
        result = provider._folk_place()

    assert result == "Offingatun"


def test_possessive_place_names_the_man_who_holds_it():
    provider = OldEnglishProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Wulfstan", "burh"]):
        result = provider._possessive_place()

    assert result == "Wulfstanesburh"


def test_provider_draws_reproduce_under_a_seed():
    """
    Every draw goes through "random_element" rather than the "random" module, which is what makes a
    seeded run repeatable. Seeded per instance rather than through "Faker.seed", because that one is
    process-global and would follow the rest of the session around.
    """
    first = Faker(["en_GB"])
    first.add_provider(OldEnglishProvider)
    first.seed_instance(4711)
    second = Faker(["en_GB"])
    second.add_provider(OldEnglishProvider)
    second.seed_instance(4711)

    result = [first.first_name_male(), first.city()]

    assert result == [second.first_name_male(), second.city()]
