from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.forms.fields import WarriorMultipleChoiceField


def test_label_from_instance_offers_the_man_by_his_full_name():
    faction = FactionFactory.build(leader_id=7)
    warrior = WarriorFactory.build(id=7, name="Uthred", faction=faction)
    field = WarriorMultipleChoiceField(queryset=Warrior.objects.none())

    result = field.label_from_instance(warrior)

    assert result == f"{Warrior.LEADER_TITLE} Uthred"
