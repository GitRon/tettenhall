import pytest

from apps.item.models.item_type import ItemType
from apps.item.tests.factories.item import ItemFactory
from apps.item.tests.factories.item_type import ItemTypeFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.warrior.forms.warrior import WarriorForm


def test_init_rejects_a_field_the_form_does_not_render():
    """
    Unreachable through the view, which validates the attribute from the URL first, so the guard
    gets tested on the form directly.
    """
    with pytest.raises(RuntimeError, match="Badly configured HTMX form"):
        WarriorForm(instance=WarriorFactory.build(), htmx_field="nickname")


@pytest.mark.django_db
def test_init_builds_only_the_slot_it_renders():
    warrior = WarriorFactory()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert tuple(form.fields) == ("weapon",)


@pytest.mark.django_db
def test_init_offers_what_the_faction_has_spare():
    warrior = WarriorFactory()
    spare_weapon = ItemFactory(owner=warrior.faction, savegame=warrior.savegame)

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert list(form.fields["weapon"].queryset) == [spare_weapon]


@pytest.mark.django_db
def test_init_offers_nothing_of_the_other_slot():
    warrior = WarriorFactory()
    ItemFactory(
        owner=warrior.faction,
        savegame=warrior.savegame,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert list(form.fields["weapon"].queryset) == []


@pytest.mark.django_db
def test_init_offers_the_item_the_warrior_already_carries():
    """
    The current value has to be in the list the select is built from, or the control opens on a slot
    that looks empty.
    """
    warrior = WarriorFactory()
    warrior.weapon = ItemFactory(owner=warrior.faction, savegame=warrior.savegame)
    warrior.save()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert list(form.fields["weapon"].queryset) == [warrior.weapon]


@pytest.mark.django_db
def test_save_leaves_the_other_slot_alone():
    warrior = WarriorFactory()
    armor = ItemFactory(
        owner=warrior.faction,
        savegame=warrior.savegame,
        type=ItemTypeFactory(function=ItemType.FunctionChoices.FUNCTION_ARMOR),
    )
    warrior.armor = armor
    warrior.save()
    new_weapon = ItemFactory(owner=warrior.faction, savegame=warrior.savegame)

    form = WarriorForm(data={"weapon": new_weapon.id}, instance=warrior, htmx_field="weapon")
    assert form.is_valid() is True
    form.save()

    warrior.refresh_from_db()
    assert warrior.weapon == new_weapon
    assert warrior.armor == armor
