"""
The one place that turns a ``Culture.locale`` into the faker that names its people and its places.

It sits in the domain app rather than in a satellite because it is the only thing in the project that
knows which locale keys the culture fixture actually carries - "ang" is a row in that table, not a fact
about Faker.
"""

from faker import Faker

from apps.faker_old_english import BYNAMES, OLD_ENGLISH_BASE_LOCALE, OLD_ENGLISH_LOCALE, OldEnglishProvider


def faker_for_locale(*, locale: str) -> Faker:
    """
    A faker for one culture's locale, Old English included.

    The Old English branch is built on a base locale and then extended, because both halves of that
    are forced: ``Faker(["ang"])`` raises - a third party cannot inject a locale - and
    ``add_provider()`` is unsupported on a multi-locale instance, so the list stays one element long.
    Only the methods the provider shadows come out Old English; anything else the game asks of that
    instance answers in the base locale.
    """
    if locale != OLD_ENGLISH_LOCALE:
        return Faker([locale])

    faker = Faker([OLD_ENGLISH_BASE_LOCALE])
    faker.add_provider(OldEnglishProvider)

    return faker


def bynames_for_locale(*, locale: str) -> tuple[str, ...]:
    """
    The bynames a name in this locale can be told apart by, empty where we have none.

    A locale we have no name stock for gets no bynames rather than English ones: "Bjørn Cild" would
    name the culture wrongly to make the roster read cleanly, which is the trade the whole provider
    exists to refuse.
    """
    if locale == OLD_ENGLISH_LOCALE:
        return BYNAMES

    return ()
