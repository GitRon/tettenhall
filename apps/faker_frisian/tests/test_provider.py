from unittest import mock

from faker import Faker
from faker.generator import Generator

from apps.faker_frisian.data import GIVEN_NAMES
from apps.faker_frisian.provider import FRISIAN_BASE_LOCALE, FrisianProvider, compound, folk_stem, genitive


def test_folk_stem_drops_a_final_vowel():
    """
    "Folka" gives "Folkingum", never "Folkaingum".
    """
    result = folk_stem(name="Folka")

    assert result == "Folk"


def test_folk_stem_keeps_a_final_consonant():
    result = folk_stem(name="Adward")

    assert result == "Adward"


def test_genitive_leaves_a_weak_name_alone():
    """
    The weak genitive singular is "-a", the same as the nominative - and the one place Frisian and Old
    English part company visibly, the latter writing "Ubban-".
    """
    result = genitive(name="Ubba")

    assert result == "Ubba"


def test_genitive_adds_the_strong_ending():
    result = genitive(name="Folkmer")

    assert result == "Folkmeres"


def test_compound_writes_a_doubled_consonant_once():
    result = compound(stem="Berg", generic="ga")

    assert result == "Berga"


def test_compound_writes_no_hiatus():
    """
    "Ubbum", not "Ubbaum" - a vowel-final stem gives its vowel up to a vowel-initial generic.
    """
    result = compound(stem="Ubba", generic="um")

    assert result == "Ubbum"


def test_compound_joins_anything_else_as_it_stands():
    result = compound(stem="Ald", generic="werd")

    assert result == "Aldwerd"


def test_first_name_male_is_drawn_from_the_pool():
    provider = FrisianProvider(Generator())

    result = provider.first_name_male()

    assert result in GIVEN_NAMES


def test_provider_draws_with_weighting():
    """
    Faker only sets this while building a factory of its own, so a provider handed in through
    "add_provider" carries the class default - and with weighting off the weights on the place-name
    patterns are read, discarded and replaced by a uniform draw, with nothing to see from the outside.
    """
    result = FrisianProvider.__use_weighting__

    assert result is True


def test_city_composes_the_pattern_it_drew():
    """
    The first draw picks the pattern, the rest of them fill it in.
    """
    provider = FrisianProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=[provider._descriptive_place, "Ald", "werd"]):
        result = provider.city()

    assert result == "Aldwerd"


def test_descriptive_place_names_what_the_land_is_like():
    provider = FrisianProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Sten", "buren"]):
        result = provider._descriptive_place()

    assert result == "Stenburen"


def test_possessive_place_names_the_man_who_holds_it():
    provider = FrisianProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Folkmer", "um"]):
        result = provider._possessive_place()

    assert result == "Folkmeresum"


def test_folk_place_names_the_men_descended_from_him():
    provider = FrisianProvider(Generator())

    with mock.patch.object(provider, "random_element", side_effect=["Folka"]):
        result = provider._folk_place()

    assert result == "Folkingum"


def test_provider_draws_reproduce_under_a_seed():
    """
    Every draw goes through "random_element" rather than the "random" module, which is what makes a
    seeded run repeatable. Seeded per instance rather than through "Faker.seed", because that one is
    process-global and would follow the rest of the session around.
    """
    first = Faker([FRISIAN_BASE_LOCALE])
    first.add_provider(FrisianProvider)
    first.seed_instance(4711)
    second = Faker([FRISIAN_BASE_LOCALE])
    second.add_provider(FrisianProvider)
    second.seed_instance(4711)

    result = [first.first_name_male(), first.city()]

    assert result == [second.first_name_male(), second.city()]
