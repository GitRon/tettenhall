from django.db import models


class ModifiedAttributeChoices(models.TextChoices):
    """
    The attributes a lasting modifier may touch - an injury or a trait.

    Strength and dexterity only. A moved "max_health" needs "current_health" clamped, moves the death
    threshold that is its own basis, and changes which men the monthly sweep selects - all solvable, and
    none of it worth it for the first sources on the layer.

    One set for every source, because the effect layer on "Warrior" groups each source's rows by this
    value and reads them back under the same key - see docs/patterns/attribute-modifiers.md. Spelled as
    the field name on "Warrior", but never fed to "getattr": the values that reach these columns come
    from a fixture rather than from a request, and the readers on the warrior name their attribute
    outright.
    """

    ATTRIBUTE_STRENGTH = "strength", "Strength"
    ATTRIBUTE_DEXTERITY = "dexterity", "Dexterity"
