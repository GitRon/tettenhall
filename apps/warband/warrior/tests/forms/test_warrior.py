import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.tests.factories.item import ItemFactory
from apps.warband.item.tests.factories.item_type import ItemTypeFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.forms.warrior import WarriorForm


@pytest.mark.django_db
def test_label_from_instance_names_a_weapon_by_its_average_damage():
    """
    Asked through the form rather than of the field on its own, so the slot is shown to be built
    from the field that carries the figures at all.
    """
    warrior = WarriorFactory()
    weapon = ItemFactory(
        type=ItemTypeFactory(name="Battle axe", base_value="1d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        condition=Item.ConditionChoices.CONDITION_RUSTY,
        modifier=1,
        owner=warrior.faction,
        savegame=warrior.savegame,
    )

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert form.fields["weapon"].label_from_instance(weapon) == "Rusty Battle axe (1d6+1) - 4.5 damage on average"


@pytest.mark.django_db
def test_label_from_instance_names_armour_by_its_average_protection():
    warrior = WarriorFactory()
    armor = ItemFactory(
        type=ItemTypeFactory(
            name="Studded leather", base_value="2d3", function=ItemType.FunctionChoices.FUNCTION_ARMOR
        ),
        owner=warrior.faction,
        savegame=warrior.savegame,
    )

    form = WarriorForm(instance=warrior, htmx_field="armor")

    assert (
        form.fields["armor"].label_from_instance(armor)
        == "Traditional Studded leather (2d3+0) - 4 protection on average"
    )


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
def test_init_offers_what_another_warrior_is_carrying():
    """
    The whole of the cascade problem. While a slot listed only spare items, moving a sword down the
    line meant re-equipping its holder first to release it, and a player who started at the man he
    wanted to arm saw a list without the sword and no way to learn why.
    """
    warrior = WarriorFactory()
    holder = WarriorFactory(faction=warrior.faction)
    holder.weapon = ItemFactory(owner=warrior.faction, savegame=warrior.savegame)
    holder.save()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert list(form.fields["weapon"].queryset) == [holder.weapon]


@pytest.mark.django_db
def test_init_offers_nothing_of_another_faction():
    warrior = WarriorFactory()
    rival = WarriorFactory(faction=FactionFactory(savegame=warrior.savegame))
    rival.weapon = ItemFactory(owner=rival.faction, savegame=warrior.savegame)
    rival.save()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert list(form.fields["weapon"].queryset) == []


@pytest.mark.django_db
def test_label_from_instance_names_the_man_an_item_would_be_taken_off():
    """
    An option that did not say so would spring the far end of a swap on the player after the save.
    """
    warrior = WarriorFactory()
    holder = WarriorFactory(faction=warrior.faction, name="Wulfric")
    holder.weapon = ItemFactory(
        type=ItemTypeFactory(name="Long sword", base_value="1d6", function=ItemType.FunctionChoices.FUNCTION_WEAPON),
        condition=Item.ConditionChoices.CONDITION_SUPERIOR,
        owner=warrior.faction,
        savegame=warrior.savegame,
    )
    holder.save()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert form.fields["weapon"].label_from_instance(holder.weapon) == (
        "Superior Long sword (1d6+0) - 3.5 damage on average, carried by Wulfric"
    )


@pytest.mark.django_db
def test_label_from_instance_does_not_name_the_slot_s_own_man():
    """
    He is the current value of the select, and "carried by" against his own name reads as a second
    person standing between him and his sword.
    """
    warrior = WarriorFactory(name="Eadric")
    warrior.weapon = ItemFactory(owner=warrior.faction, savegame=warrior.savegame)
    warrior.save()

    form = WarriorForm(instance=warrior, htmx_field="weapon")

    assert "carried by" not in form.fields["weapon"].label_from_instance(warrior.weapon)
