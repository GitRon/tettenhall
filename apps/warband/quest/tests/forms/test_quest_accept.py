import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.forms.quest_accept import QuestAcceptForm
from apps.warband.quest.quests.drive_off_wolves import DriveOffWolves
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.availability import REASON_SWORN_TO_A_QUEST


@pytest.mark.django_db
def test_quest_accept_form_draws_a_man_away_on_another_quest_with_his_reason():
    """He is drawn, greyed and carrying why, rather than left out."""
    quest = QuestFactory(month=2)
    away_warrior = WarriorFactory(faction=quest.faction)
    QuestContractFactory(faction=quest.faction, accepted_in_month=2, assigned_warriors=[away_warrior])

    form = QuestAcceptForm(quest=quest, month=2)

    assert list(form.fields["assigned_warriors"].queryset) == [away_warrior]
    assert form.roster.reasons_by_warrior_id == {away_warrior.id: REASON_SWORN_TO_A_QUEST}


@pytest.mark.django_db
def test_quest_accept_form_leaves_out_another_factions_man():
    quest = QuestFactory(month=2)
    WarriorFactory(faction=FactionFactory(savegame=quest.faction.savegame))

    form = QuestAcceptForm(quest=quest, month=2)

    assert list(form.fields["assigned_warriors"].queryset) == []


@pytest.mark.django_db
def test_quest_accept_form_says_so_when_nobody_can_go():
    quest = QuestFactory(month=2)
    away_warrior = WarriorFactory(faction=quest.faction)
    QuestContractFactory(faction=quest.faction, accepted_in_month=2, assigned_warriors=[away_warrior])

    form = QuestAcceptForm(quest=quest, month=2)

    assert form.fields["assigned_warriors"].help_text == QuestAcceptForm.NOBODY_AVAILABLE


@pytest.mark.django_db
def test_quest_accept_form_is_valid_for_a_band_it_takes():
    quest = QuestFactory(month=2)
    warrior = WarriorFactory(faction=quest.faction)

    form = QuestAcceptForm(data={"assigned_warriors": [warrior.id]}, quest=quest, month=2)

    assert form.is_valid() is True


@pytest.mark.django_db
def test_quest_accept_form_refuses_a_man_who_is_away():
    """A hand-edited post: the greyed box is disabled in the browser and nowhere else."""
    quest = QuestFactory(month=2)
    away_warrior = WarriorFactory(faction=quest.faction, name="Wulfstan")
    QuestContractFactory(faction=quest.faction, accepted_in_month=2, assigned_warriors=[away_warrior])

    form = QuestAcceptForm(data={"assigned_warriors": [away_warrior.id]}, quest=quest, month=2)

    assert form.is_valid() is False
    assert form.errors["assigned_warriors"] == ["Wulfstan cannot be sent on a quest this month."]


@pytest.mark.django_db
def test_quest_accept_form_refuses_too_few_men():
    quest = QuestFactory(month=2, quest=DriveOffWolves.__name__)
    warrior = WarriorFactory(faction=quest.faction)

    form = QuestAcceptForm(data={"assigned_warriors": [warrior.id]}, quest=quest, month=2)

    assert form.is_valid() is False
    assert form.errors["assigned_warriors"] == ["This quest takes 2 to 4 men."]


@pytest.mark.django_db
def test_quest_accept_form_refuses_too_many_men():
    quest = QuestFactory(month=2, quest=DriveOffWolves.__name__)
    warriors = WarriorFactory.create_batch(5, faction=quest.faction)

    form = QuestAcceptForm(data={"assigned_warriors": [warrior.id for warrior in warriors]}, quest=quest, month=2)

    assert form.is_valid() is False
    assert form.errors["assigned_warriors"] == ["This quest takes 2 to 4 men."]
