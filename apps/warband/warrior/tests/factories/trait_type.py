import factory
from factory.django import DjangoModelFactory

from apps.warband.warrior.choices.modified_attribute import ModifiedAttributeChoices
from apps.warband.warrior.models.trait_type import TraitType


class TraitTypeFactory(DjangoModelFactory):
    """
    A trait type for a test that needs a *specific* one.

    The shipped catalogue is reference data and is loaded session-wide, so a test asserting on what the
    game actually draws or grants reads that rather than building a look-alike here - see
    docs/patterns/testing-data.md.
    """

    class Meta:
        model = TraitType

    name = factory.Sequence(lambda n: f"Trait type {n}")
    hook = factory.Sequence(lambda n: f"trait-type-{n}")
    group = factory.Sequence(lambda n: f"group-{n}")
    attribute = ModifiedAttributeChoices.ATTRIBUTE_STRENGTH
    magnitude = 1
    source = TraitType.SourceChoices.SOURCE_INNATE
