from django.db import models


class InjuryType(models.Model):
    """
    A kind of lasting harm a beating can leave behind: what it is called, and what it costs.

    Reference data, the way "Culture" and "ItemType" are - a fixture at the app root, so the
    catalogue stays editable without a migration. What each entry costs is a balance number and
    follows docs/patterns/town-buildings.md.

    Its own table rather than one shared with the traits #119 wants. What the two share is the effect
    layer below (docs/patterns/attribute-modifiers.md), not the reference data above it: a trait needs
    an exclusive-group key, a sign, a source and a hook the incident pool selects on, none of which an
    injury has, and one table for both would carry a kind discriminator and a column set that is dead
    for half the rows.
    """

    class AttributeChoices(models.TextChoices):
        """
        The attributes an injury may touch.

        Strength and dexterity only. A dropped "max_health" needs "current_health" clamped, moves the
        death threshold that is its own basis, and changes which men the monthly sweep selects - all
        solvable, and none of it worth it for the first injury.

        Spelled as the field name on "Warrior" so the effect layer can group by it, but never fed to
        "getattr": the values that reach this column come from a fixture rather than from a request,
        and the two readers on the warrior name their attribute outright.
        """

        ATTRIBUTE_STRENGTH = "strength", "Strength"
        ATTRIBUTE_DEXTERITY = "dexterity", "Dexterity"

    name = models.CharField("Name", max_length=75)
    attribute = models.CharField("Attribute", choices=AttributeChoices.choices, max_length=20)
    # Points off the attribute, against archetype means of 5 for a levy, 8 for a leader and 10 for a
    # mercenary. One or two: three would be over half of what a fyrd man has to give.
    magnitude = models.PositiveSmallIntegerField("Magnitude")

    class Meta:
        verbose_name = "Injury type"
        verbose_name_plural = "Injury types"
        default_related_name = "injury_types"

    def __str__(self) -> str:
        return self.name

    @property
    def description(self) -> str:
        """
        The injury as it is put to the player: the thing, and what it takes off him.
        """
        return f"{self.name} (-{self.magnitude} {self.get_attribute_display()})"
