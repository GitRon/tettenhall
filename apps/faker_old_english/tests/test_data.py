import re

from apps.faker_old_english.data import BYNAMES, GIVEN_NAMES, PLACE_ELEMENTS, PLACE_GENERICS

ORTHOGRAPHY = re.compile(r"[A-Za-z]+")


def test_given_names_hold_no_duplicate():
    """
    A duplicate is a name drawn twice as often as the rest, and the pool is long enough that nobody
    would spot one by reading it.
    """
    result = len(set(GIVEN_NAMES))

    assert result == len(GIVEN_NAMES)


def test_given_names_obey_the_orthography():
    """
    "ae" written out, thorn and eth resolved to "th", no macrons and no Latin - which together mean
    every name is plain ASCII letters.
    """
    result = [name for name in GIVEN_NAMES if not ORTHOGRAPHY.fullmatch(name)]

    assert result == []


def test_place_elements_obey_the_orthography():
    result = [element for element in PLACE_ELEMENTS if not ORTHOGRAPHY.fullmatch(element)]

    assert result == []


def test_place_generics_obey_the_orthography():
    result = [generic for generic in PLACE_GENERICS if not ORTHOGRAPHY.fullmatch(generic)]

    assert result == []


def test_bynames_obey_the_orthography():
    result = [byname for byname in BYNAMES if not ORTHOGRAPHY.fullmatch(byname)]

    assert result == []


def test_no_generic_is_also_an_element():
    """
    A generic that is also a first element would compose with itself, and the place would read as two
    settlements stuck together.
    """
    result = {generic.capitalize() for generic in PLACE_GENERICS} & set(PLACE_ELEMENTS)

    assert result == set()
