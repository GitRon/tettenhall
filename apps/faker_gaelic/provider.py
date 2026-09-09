"""
A Faker provider for Old Irish given names and place names.

Faker cannot be taught a locale from outside: ``Faker(["sga"])`` normalises the string and checks it
against ``faker.config.AVAILABLE_LOCALES``, raising before it imports a single provider. So "sga" is
this project's own key for the Gaelic name stock, and the way in is ``Faker.add_provider()`` on a
single-locale instance - see the factory that builds one.

The provider shadows Faker's own ``first_name_male`` and ``city``, so a caller holding the instance
asks for exactly what it always asked for. Faker ships an Irish person provider but no Irish address
provider, which is why a settlement needs one here at all.

Place names compose in three patterns, all of them a generic followed by a genitive or an adjective -
the Irish order, where English would compound the two into one word:

- **Possessive.** The man who holds it, in the genitive: "Dún Cormaic".
- **Feature.** What the land holds, in the genitive: "Cill Dara", the church of the oak.
- **Qualified.** An adjective: "Ráth Mhór".

What follows a **feminine** generic is lenited, and what follows a masculine one is not - "Cill
Chiaráin" against "Dún Cormaic". Lenition writes an "h" after the initial consonant, and three things
stop it:

- **A word that cannot be lenited at all**: one beginning with a vowel, or with "l", "n" or "r".
- **An "s" before a stop or an "m"**: "Scandláin" stays as it is, where "Sailech" gives "Shailech".
- **The dentals rule.** A "d", "t" or "s" is not lenited where the generic itself ends in one of
  "d", "n", "t", "l", "s", because the two sounds run together. This is what makes the church of the
  oak "Cill Dara" rather than "Cill Dhara".

Every draw goes through ``self.random_element`` rather than the ``random`` module, so ``Faker.seed()``
reproduces a run.
"""

from collections import OrderedDict

from faker.providers import BaseProvider

from apps.faker_gaelic.data import (
    FEATURE_GENITIVES,
    FEMININE,
    GIVEN_NAMES,
    PLACE_GENERICS,
    PLACE_QUALIFIERS,
    PlaceGeneric,
)

# What "Culture.locale" carries for the Irish culture: the ISO 639-3 code for Old Irish, the language
# of 910. Not a Faker locale, and not something we can make into one - Faker accepts the locales it
# ships provider data for and nothing else, so any key we picked would be refused the same way. A
# standard code at least tells a reader what the row means.
GAELIC_LOCALE = "sga"

# The locale a provider-equipped instance is built on, and therefore what everything this provider
# does *not* shadow comes out as. Irish English rather than British: whatever else the game asks of
# that instance should answer from the same island.
GAELIC_BASE_LOCALE = "en_IE"

# The initial consonants lenition can touch. A vowel takes none, and neither do "l", "n" and "r".
LENITABLE_INITIALS = "bcdfgmpst"

# An "s" before one of these is part of a cluster that resists lenition. Before anything else - a
# vowel, "l", "n", "r" - it lenites like any other consonant.
UNLENITABLE_AFTER_S = ("c", "m", "p", "t")

# The dentals rule: a "d", "t" or "s" is not lenited where the word in front of it ends in one of
# these, the two sounds being too close to hold apart.
DENTALS = "dntls"
DENTAL_INITIALS = "dts"


def lenite(*, word: str, preceding: str) -> str:
    """
    The word as it is written after something that lenites it, which may be unchanged.
    """
    initial = word[0].lower()

    if initial not in LENITABLE_INITIALS:
        return word

    if initial == "s" and word[1:2].lower() in UNLENITABLE_AFTER_S:
        return word

    if initial in DENTAL_INITIALS and preceding[-1].lower() in DENTALS:
        return word

    return f"{word[0]}h{word[1:]}"


def compose(*, generic: PlaceGeneric, qualifier: str) -> str:
    """
    A place name: the generic, a space, and what qualifies it, lenited where the generic is feminine.
    """
    if generic.gender == FEMININE:
        return f"{generic.word} {lenite(word=qualifier, preceding=generic.word)}"

    return f"{generic.word} {qualifier}"


class GaelicProvider(BaseProvider):
    # Faker sets this per provider while it builds a factory and therefore never for one handed in
    # through "add_provider", where it stays at the class default of False - and a weighted draw with
    # weighting off silently falls back to a uniform one.
    __use_weighting__ = True

    def first_name_male(self) -> str:
        return self.random_element(GIVEN_NAMES).nominative

    def city(self) -> str:
        # The three patterns draw on pools an order of magnitude apart - two hundred given names
        # against thirty features and twenty-three adjectives - so an even draw would leave the
        # personal names all distinct while a "Ráth Mhór" came round again and again. The weights
        # answer that and still leave three names in five taken from the land or from a quality
        # rather than from a man, which is what keeps a rivals list readable.
        #
        # An OrderedDict rather than a dict because Faker refuses the latter for a weighted draw: the
        # iteration order of a dict follows PYTHONHASHSEED, which would move the weights onto other
        # patterns from one process to the next.
        pattern = self.random_element(
            OrderedDict(
                (
                    (self._possessive_place, 0.4),
                    (self._feature_place, 0.35),
                    (self._qualified_place, 0.25),
                )
            )
        )

        return pattern()

    def _possessive_place(self) -> str:
        return compose(generic=self.random_element(PLACE_GENERICS), qualifier=self.random_element(GIVEN_NAMES).genitive)

    def _feature_place(self) -> str:
        return compose(generic=self.random_element(PLACE_GENERICS), qualifier=self.random_element(FEATURE_GENITIVES))

    def _qualified_place(self) -> str:
        return compose(generic=self.random_element(PLACE_GENERICS), qualifier=self.random_element(PLACE_QUALIFIERS))
