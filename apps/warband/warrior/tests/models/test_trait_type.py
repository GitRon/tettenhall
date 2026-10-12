import pytest

from apps.warband.warrior.models.trait_type import TraitType
from apps.warband.warrior.tests.factories.trait_type import TraitTypeFactory


@pytest.mark.django_db
def test_str_is_the_name():
    trait_type = TraitTypeFactory(name="Drunkard")

    assert str(trait_type) == "Drunkard"


@pytest.mark.django_db
def test_hook_of_every_shipped_earned_trait_has_a_rule():
    """
    Every earned row needs a rule in "TraitEarningService", which finds its row by the hook.
    """
    earned_hooks = set(
        TraitType.objects.filter(source=TraitType.SourceChoices.SOURCE_EARNED).values_list("hook", flat=True)
    )

    assert earned_hooks == {"shaken", "charmed", "headtaker", "shield-wall-man"}
