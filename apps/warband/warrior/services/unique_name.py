"""
Drawing a warrior a name no living man in the savegame already answers to.

A pool of names is not enough on its own. Even at the 339 given names of the largest of them, the
chance that twenty living warriors hold a duplicate between them is 43% - the birthday problem, not a
small pool - and two men called Wulfstan in one war band is a bug report about the roster, not
flavour.
"""

from apps.warband.faction.models.culture import Culture
from apps.warband.faction.services.faker import bynames_for_locale, faker_for_locale
from apps.warband.skirmish.models.warrior import Warrior

# How many times a colliding draw is simply repeated before the name gets disambiguated instead. Five,
# because a redraw only fails again with the probability of the first collision: against forty living
# warriors out of 339 names that is a chance in forty thousand, and every attempt past that is a query
# nobody will ever benefit from.
NAME_DRAW_ATTEMPTS = 5


def _disambiguate(*, name: str, names_in_play: set[str], locale: str) -> str:
    """
    The same name, told apart from the man who already has it.

    A byname first - "Aelfric Cild" is how a charter separates two Aelfrics - and a number once those
    are used up, which needs a war band holding every byname on the same given name to ever be seen.
    """
    for byname in bynames_for_locale(locale=locale):
        candidate = f"{name} {byname}"
        if candidate not in names_in_play:
            return candidate

    ordinal = 2
    while f"{name} {ordinal}" in names_in_play:
        ordinal += 1

    return f"{name} {ordinal}"


def draw_warrior_name(*, culture: Culture, savegame_id: int) -> str:
    """
    A given name for a new warrior, unique among the warriors still in play in this savegame.

    Uniqueness is against the living rather than against every row ever written, because a long game
    writes hundreds of dead men and would drive every draw into the fallback - and because a fallen
    warrior's name is free again in the way the game means it. It is not a database constraint for the
    same reason: the rule is per savegame and per condition, and a column cannot say that.

    ``fake.unique`` is no help here either. The generator builds a faker per warrior, so its memory is
    empty every time.
    """
    faker = faker_for_locale(locale=culture.locale)
    names_in_play = set(
        Warrior.objects.filter(savegame_id=savegame_id)
        .exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)
        .values_list("name", flat=True)
    )

    name = faker.first_name_male()
    attempts = 1
    while name in names_in_play and attempts < NAME_DRAW_ATTEMPTS:
        name = faker.first_name_male()
        attempts += 1

    if name in names_in_play:
        return _disambiguate(name=name, names_in_play=names_in_play, locale=culture.locale)

    return name
