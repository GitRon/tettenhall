from django.db import models


class NicknameStateChoices(models.IntegerChoices):
    """
    What a warrior is named for: how his attributes stand, or something he did.

    An attribute epithet is drawn, a deed epithet awarded, and a man carries one of them at a time. The
    first deed he does replaces an attribute epithet, and after that nothing renames him for the rest
    of the savegame.

    The state and not the wording: which of the several synonyms phrases it is the warrior's own
    "nickname_variant", so the lists in "apps.warband.warrior.services.nickname" stay editable and a
    man already made is re-read through whatever they say today.

    Its own module rather than the service that draws it, because a model field's choices have to be
    importable by the model, and the model already imports the service for its rules.
    """

    STRENGTH = 1, "Strength, past the near threshold"
    STRENGTH_FAR = 2, "Strength, past the far threshold"
    DEXTERITY = 3, "Dexterity, past the near threshold"
    DEXTERITY_FAR = 4, "Dexterity, past the far threshold"
    HEALTH = 5, "Health, past the near threshold"
    HEALTH_FAR = 6, "Health, past the far threshold"
    MORALE = 7, "Morale, past the near threshold"
    MORALE_FAR = 8, "Morale, past the far threshold"
    # One state for both arms rather than one each: they are drawn from the same trio, and read
    # together as a sum they name the feeblest of a kind rather than one man in ten per arm
    STATS_AT_BOTTOM = 9, "Both arms at the bottom"
    HEALTH_AT_BOTTOM = 10, "Health at the bottom"
    MORALE_AT_BOTTOM = 11, "Morale at the bottom"

    # What he did rather than what he rolled. Numbered apart from the attribute states so the two
    # families read as two at a glance in the database; which family a state belongs to is
    # [DEED_NICKNAME_STATES], not the number
    RELIC_BEARER = 101, "Carried the hall's relic"
    LORD_SLAYER = 102, "Killed a faction's leader in a fight"
    WALLBREAKER = 103, "Brought down the walls he was storming"
    GIANTBANE = 104, "Put down a man far above him"
    UNBROKEN = 105, "The last man standing on a winning side"
    OLD_WOLF = 106, "Came home from many fights"


# The states a man is named for a deed. The one difference between the families that anything acts on:
# an attribute epithet gives way to the first deed a man does, and a deed epithet gives way to nothing -
# see [handle_award_deed_nickname]
DEED_NICKNAME_STATES = frozenset(
    {
        NicknameStateChoices.RELIC_BEARER,
        NicknameStateChoices.LORD_SLAYER,
        NicknameStateChoices.WALLBREAKER,
        NicknameStateChoices.GIANTBANE,
        NicknameStateChoices.UNBROKEN,
        NicknameStateChoices.OLD_WOLF,
    }
)
