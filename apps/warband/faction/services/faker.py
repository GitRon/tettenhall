"""
The one place that turns a ``Culture.locale`` into the faker that names its people and its places.

It sits in the domain app rather than in a satellite because it is the only thing in the project that
knows which locale keys the culture fixture actually carries - "ang" and "sga" are rows in that table,
not facts about Faker.
"""

from faker import Faker
from faker.providers import BaseProvider

from apps.faker_gaelic import BYNAMES as GAELIC_BYNAMES
from apps.faker_gaelic import GAELIC_BASE_LOCALE, GAELIC_LOCALE, GaelicProvider
from apps.faker_old_english import BYNAMES as OLD_ENGLISH_BYNAMES
from apps.faker_old_english import OLD_ENGLISH_BASE_LOCALE, OLD_ENGLISH_LOCALE, OldEnglishProvider

# The locale keys we hold our own name stock for, each with the base locale its instance stands on. A
# key lands here rather than in Faker for the same reason every time: Faker accepts the locales it
# ships provider data for and refuses anything else, so a language it has none for cannot be injected
# and has to be added on top of one it does have.
PROVIDERS_BY_LOCALE: dict[str, tuple[str, type[BaseProvider]]] = {
    OLD_ENGLISH_LOCALE: (OLD_ENGLISH_BASE_LOCALE, OldEnglishProvider),
    GAELIC_LOCALE: (GAELIC_BASE_LOCALE, GaelicProvider),
}

BYNAMES_BY_LOCALE: dict[str, tuple[str, ...]] = {
    OLD_ENGLISH_LOCALE: OLD_ENGLISH_BYNAMES,
    GAELIC_LOCALE: GAELIC_BYNAMES,
}


def faker_for_locale(*, locale: str) -> Faker:
    """
    A faker for one culture's locale, ours included.

    One of ours is built on a base locale and then extended, because both halves of that are forced:
    ``Faker(["ang"])`` raises - a third party cannot inject a locale - and ``add_provider()`` is
    unsupported on a multi-locale instance, so the list stays one element long. Only the methods the
    provider shadows come out in its own language; anything else the game asks of that instance
    answers in the base locale.
    """
    if locale not in PROVIDERS_BY_LOCALE:
        return Faker([locale])

    base_locale, provider = PROVIDERS_BY_LOCALE[locale]
    faker = Faker([base_locale])
    faker.add_provider(provider)

    return faker


def bynames_for_locale(*, locale: str) -> tuple[str, ...]:
    """
    The bynames a name in this locale can be told apart by, empty where we have none.

    A locale we have no name stock for gets no bynames rather than English ones: "Bjørn Cild" would
    name the culture wrongly to make the roster read cleanly, which is the trade the whole provider
    exists to refuse.
    """
    return BYNAMES_BY_LOCALE.get(locale, ())
