from django.db import models

from apps.warband.warrior.choices.modified_attribute import ModifiedAttributeChoices


class TraitType(models.Model):
    """
    A kind of man a warrior can be: what it is called, what it does to him, and how he comes by it.

    Reference data, the way "InjuryType" is - a fixture at the app root, so the catalogue stays editable
    without a migration. What each entry is worth is a balance number and follows
    docs/patterns/town-buildings.md.

    Its own table rather than one shared with [InjuryType], see docs/patterns/attribute-modifiers.md:
    the two share the effect layer on "Warrior" and nothing above it.

    Never shown to the player. A drunk you can spot in the pub is a price negotiation; one you discover
    in month three is a story, so nothing renders a trait - the player finds one out through the fights
    it changes.
    """

    class SourceChoices(models.TextChoices):
        # Drawn by the generator alongside the attribute rolls, and never granted afterwards
        SOURCE_INNATE = "innate", "Innate"
        # Granted after a fight off the blow record, and never drawn at generation
        SOURCE_EARNED = "earned", "Earned"

    name = models.CharField("Name", max_length=75)
    # The one key every reader names a trait by: the earning rules find their own row through it, and it
    # is what an incident will ask a man about when the incident pool learns to weight its draw
    hook = models.SlugField("Hook", max_length=30, unique=True)
    # No man carries two traits of one group. "Steady" and "Shaken" on the same warrior is a bug rather
    # than a person, and saying so here is what spares the effect layer a rule for combining them
    group = models.SlugField("Group", max_length=30)
    attribute = models.CharField("Attribute", choices=ModifiedAttributeChoices.choices, max_length=20)
    # Points on the attribute, signed: a trait can be a virtue. One point either way against archetype
    # means of 5 for a levy, 8 for a leader and 10 for a mercenary
    magnitude = models.SmallIntegerField("Magnitude")
    source = models.CharField("Source", choices=SourceChoices.choices, max_length=10)

    class Meta:
        verbose_name = "Trait type"
        verbose_name_plural = "Trait types"
        default_related_name = "trait_types"
        # The order the earning rules are asked in, so which of two traits a fight grants is the
        # catalogue's call and not the database's
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name
