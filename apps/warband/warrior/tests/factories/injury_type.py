import factory
from factory.django import DjangoModelFactory

from apps.warband.warrior.models.injury_type import InjuryType


class InjuryTypeFactory(DjangoModelFactory):
    """
    An injury type for a test that needs a *specific* one.

    The shipped catalogue is reference data and is loaded session-wide, so a test asserting on what
    the game actually inflicts reads that rather than building a look-alike here - see
    docs/patterns/testing-data.md.
    """

    class Meta:
        model = InjuryType

    name = factory.Sequence(lambda n: f"Injury type {n}")
    attribute = InjuryType.AttributeChoices.ATTRIBUTE_STRENGTH
    magnitude = 1
