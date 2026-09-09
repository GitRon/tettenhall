import re

from apps.faker_gaelic.data import (
    BYNAMES,
    FEATURE_GENITIVES,
    FEMININE,
    GIVEN_NAMES,
    MASCULINE,
    PLACE_GENERICS,
    PLACE_QUALIFIERS,
)

# Letters and the length mark, and nothing else: no manuscript abbreviation, no lenition dot, and no
# space, the two-element names being left out on purpose.
ORTHOGRAPHY = re.compile(r"[A-Za-zÁÉÍÓÚáéíóú]+")


def test_given_names_hold_no_duplicate():
    """
    A duplicate is a name drawn twice as often as the rest, and the pool is long enough that nobody
    would spot one by reading it.
    """
    result = len({name.nominative for name in GIVEN_NAMES})

    assert result == len(GIVEN_NAMES)


def test_given_names_obey_the_orthography():
    """
    Both columns: a genitive is as visible to the player as a nominative, since it is what a town is
    named after.
    """
    result = [
        form for name in GIVEN_NAMES for form in (name.nominative, name.genitive) if not ORTHOGRAPHY.fullmatch(form)
    ]

    assert result == []


def test_place_generics_obey_the_orthography():
    result = [generic.word for generic in PLACE_GENERICS if not ORTHOGRAPHY.fullmatch(generic.word)]

    assert result == []


def test_place_generics_carry_a_gender():
    """
    A generic with anything else in that column would silently stop lenition, since only the feminine
    branch does any.
    """
    result = [generic.word for generic in PLACE_GENERICS if generic.gender not in (FEMININE, MASCULINE)]

    assert result == []


def test_place_qualifiers_obey_the_orthography():
    result = [qualifier for qualifier in PLACE_QUALIFIERS if not ORTHOGRAPHY.fullmatch(qualifier)]

    assert result == []


def test_feature_genitives_obey_the_orthography():
    result = [feature for feature in FEATURE_GENITIVES if not ORTHOGRAPHY.fullmatch(feature)]

    assert result == []


def test_bynames_obey_the_orthography():
    result = [byname for byname in BYNAMES if not ORTHOGRAPHY.fullmatch(byname)]

    assert result == []


def test_no_qualifier_is_also_a_generic():
    """
    A generic in the adjective slot would read as two settlements standing next to each other.
    """
    result = set(PLACE_QUALIFIERS) & {generic.word for generic in PLACE_GENERICS}

    assert result == set()


def test_no_feature_is_also_a_generic():
    """
    And a generic in the feature slot would name the fort of the fort.
    """
    result = set(FEATURE_GENITIVES) & {generic.word for generic in PLACE_GENERICS}

    assert result == set()
