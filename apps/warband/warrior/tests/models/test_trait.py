import pytest
from django.db import IntegrityError

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.trait import Trait
from apps.warband.warrior.tests.factories.trait import TraitFactory
from apps.warband.warrior.tests.factories.trait_type import TraitTypeFactory


@pytest.mark.django_db
def test_str_names_the_man_and_the_trait():
    trait = TraitFactory(warrior__name="Cuthred", type__name="Drunkard")

    assert str(trait) == "Cuthred: Drunkard"


@pytest.mark.django_db
def test_create_record_writes_the_row():
    warrior = WarriorFactory()
    trait_type = TraitTypeFactory()

    trait = Trait.objects.create_record(warrior=warrior, trait_type=trait_type)

    assert list(warrior.traits.all()) == [trait]


@pytest.mark.django_db
def test_a_man_carries_a_kind_of_trait_once():
    trait = TraitFactory()

    with pytest.raises(IntegrityError):
        Trait.objects.create_record(warrior=trait.warrior, trait_type=trait.type)


@pytest.mark.django_db
def test_for_warrior_narrows_to_one_man():
    trait = TraitFactory()
    TraitFactory()

    result = Trait.objects.for_warrior(warrior_id=trait.warrior_id)

    assert list(result) == [trait]
