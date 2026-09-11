from django.db import models


class NicknameStateChoices(models.IntegerChoices):
    """
    What a warrior is named for, once and for the rest of the savegame.

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
    # One state for both arms rather than one each: the two are floored at the same "STATS_MIN" and
    # the left tail of both sits on that floor, so neither says anything about somebody unusual alone
    STATS_AT_FLOOR = 9, "Both arms at the floor"
    HEALTH_AT_BOTTOM = 10, "Health at the bottom"
    MORALE_AT_BOTTOM = 11, "Morale at the bottom"
