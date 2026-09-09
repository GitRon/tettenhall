"""
A Faker provider for Old English given names and place names.

Faker cannot be taught a locale from outside: ``Faker(["ang"])`` normalises the string and checks it
against ``faker.config.AVAILABLE_LOCALES``, raising before it imports a single provider. So "ang" is
this project's own key for the Old English name stock, and the way in is ``Faker.add_provider()`` on a
single-locale instance - see the factory that builds one.

The provider shadows Faker's own ``first_name_male`` and ``city``, so a caller holding the instance
asks for exactly what it always asked for.

Place names compose in three patterns. The joining rules are the whole reason this is code rather than
a list:

- **Descriptive.** An element and a generic, "Stan" + "tun" - "Stantun".
- **Folk.** The group descended from a man, whose stem loses a final vowel before "-inga-": "Offa"
  gives "Offinga-", never "Offainga-" - "Offingatun".
- **Possessive.** The man himself, in the genitive: weak "-an" for a name ending in "-a" ("Dudda" -
  "Duddanburh"), the strong "-es" for everything else ("Wulfstan" - "Wulfstanesburh"), which absorbs
  a final "-e" rather than doubling it ("Deorwine" - "Deorwinesford").

Every draw goes through ``self.random_element`` rather than the ``random`` module, so ``Faker.seed()``
reproduces a run.
"""

from collections import OrderedDict

from faker.providers import BaseProvider

from apps.faker_old_english.data import GIVEN_NAMES, PLACE_ELEMENTS, PLACE_GENERICS

# What "Culture.locale" carries for the Saxon culture: the ISO 639-3 code for Old English. Not a Faker
# locale, and not something we can make into one - Faker accepts the locales it ships provider data for
# and nothing else, so any key we picked would be refused the same way. A standard code at least tells
# a reader what the row means.
OLD_ENGLISH_LOCALE = "ang"

# The locale a provider-equipped instance is built on, and therefore what everything this provider
# does *not* shadow comes out as. English rather than anything else, for the obvious reason.
OLD_ENGLISH_BASE_LOCALE = "en_GB"

VOWELS = "aeiouy"


def folk_stem(*, name: str) -> str:
    """
    The stem "-inga-" attaches to, which loses a final vowel to it: "Offa" gives "Off".
    """
    if name[-1].lower() in VOWELS:
        return name[:-1]

    return name


def genitive(*, name: str) -> str:
    """
    The name in the genitive: weak "-an" for the "-a" names, the strong "-es" for the rest.

    A name already ending in "-e" gives that vowel up to the ending rather than keeping it, so
    "Deorwine" is "Deorwines-" and not "Deorwinees-" - the whole "-wine" family of names goes through
    here, so it is the common case rather than a curiosity.
    """
    if name.endswith("a"):
        return f"{name}n"

    if name.endswith("e"):
        return f"{name[:-1]}es"

    return f"{name}es"


def compound(*, stem: str, generic: str) -> str:
    """
    A stem and a generic written as one word, with a consonant doubled across the seam written once.

    "Aesc" and "ceaster" make "Aesceaster" rather than "Aescceaster", which is how the compound is
    said and how the record spells it.
    """
    if stem[-1].lower() == generic[0]:
        return f"{stem[:-1]}{generic}"

    return f"{stem}{generic}"


class OldEnglishProvider(BaseProvider):
    # Faker sets this per provider while it builds a factory and therefore never for one handed in
    # through "add_provider", where it stays at the class default of False - and a weighted draw with
    # weighting off silently falls back to a uniform one.
    __use_weighting__ = True

    def first_name_male(self) -> str:
        return self.random_element(GIVEN_NAMES)

    def city(self) -> str:
        # Half the map is named after the land rather than after a man, which is both how English
        # place names fall out and what keeps a rivals list readable: a given name is dithematic and
        # the genitive adds to it, so an even draw between the three patterns makes two names in three
        # another "Aethelbeorhteshalh".
        #
        # An OrderedDict rather than a dict because Faker refuses the latter for a weighted draw: the
        # iteration order of a dict follows PYTHONHASHSEED, which would move the weights onto other
        # patterns from one process to the next.
        pattern = self.random_element(
            OrderedDict(
                (
                    (self._descriptive_place, 0.5),
                    (self._possessive_place, 0.3),
                    (self._folk_place, 0.2),
                )
            )
        )

        return pattern()

    def _descriptive_place(self) -> str:
        return compound(stem=self.random_element(PLACE_ELEMENTS), generic=self.random_element(PLACE_GENERICS))

    def _folk_place(self) -> str:
        stem = folk_stem(name=self.random_element(GIVEN_NAMES))

        return compound(stem=f"{stem}inga", generic=self.random_element(PLACE_GENERICS))

    def _possessive_place(self) -> str:
        return compound(
            stem=genitive(name=self.random_element(GIVEN_NAMES)), generic=self.random_element(PLACE_GENERICS)
        )
