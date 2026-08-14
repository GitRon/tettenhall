import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.forms.quest_accept import QuestAcceptForm
from apps.quest.tests.factories.quest import QuestFactory
from apps.quest.tests.factories.quest_contract import QuestContractFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_assignable_warriors_exclude_a_warrior_still_in_last_month_s_fight():
    """
    The month rolling over used to free a warrior up while he was still standing on the roster of a
    quest fight nobody had played out - the TODO that used to sit on this queryset.
    """
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    committed_warrior = WarriorFactory(faction=faction)
    old_contract = QuestContractFactory(faction=faction, accepted_in_month=1)
    old_contract.assigned_warriors.add(committed_warrior)
    open_skirmish = SkirmishFactory(attacking_faction=faction, month=1)
    open_skirmish.attacking_warriors.add(committed_warrior)

    new_quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(quest_id=new_quest.id, player_faction_id=faction.id)

    assert list(form.fields["assigned_warriors"].queryset) == []
