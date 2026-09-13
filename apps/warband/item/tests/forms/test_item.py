import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.forms.item import AssignItemForm
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_init_offers_the_men_of_the_owning_faction():
    warrior = WarriorFactory()
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    form = AssignItemForm(item=item)

    assert list(form.fields["warrior"].queryset) == [warrior]


@pytest.mark.django_db
def test_init_offers_nobody_of_another_faction():
    """
    Being in the same savegame is not enough - the posted id would otherwise re-arm a rival's man
    with the player's own gear.
    """
    owner = FactionFactory()
    WarriorFactory(faction=FactionFactory(savegame=owner.savegame))
    item = ItemFactory(savegame=owner.savegame, owner=owner)

    form = AssignItemForm(item=item)

    assert list(form.fields["warrior"].queryset) == []


@pytest.mark.django_db
def test_init_leaves_the_dead_out():
    warrior = WarriorFactory(condition=Warrior.ConditionChoices.CONDITION_DEAD)
    item = ItemFactory(savegame=warrior.savegame, owner=warrior.faction)

    form = AssignItemForm(item=item)

    assert list(form.fields["warrior"].queryset) == []


@pytest.mark.django_db
def test_init_offers_nobody_for_an_unowned_item():
    """
    The shop's shelf and what the pub mercenaries carry have no owner. A faction-less lookup would
    match every faction-less warrior in the savegame, which is exactly those mercenaries.
    """
    faction = FactionFactory()
    WarriorFactory(faction=None, savegame=faction.savegame, culture=faction.culture)
    item = ItemFactory(savegame=faction.savegame, owner=None)

    form = AssignItemForm(item=item)

    assert list(form.fields["warrior"].queryset) == []
