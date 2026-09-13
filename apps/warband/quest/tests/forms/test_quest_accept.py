import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.forms.quest_accept import QuestAcceptForm
from apps.warband.quest.tests.factories.quest import QuestFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.savegame.tests.factories.savegame import SavegameFactory
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.availability import REASON_STANDING_IN_AN_OPEN_FIGHT


@pytest.mark.django_db
def test_assignable_warriors_offer_a_warrior_still_in_last_month_s_fight_with_his_reason():
    """
    The exclusion this form used to perform silently. He is drawn now, greyed and carrying why - an
    absence is a prompt to do nothing, where "he is standing in a fight nobody settled" is a prompt
    to go and settle it.
    """
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    committed_warrior = WarriorFactory(faction=faction)
    old_contract = QuestContractFactory(faction=faction, accepted_in_month=1)
    old_contract.assigned_warriors.add(committed_warrior)
    open_skirmish = SkirmishFactory(attacking_faction=faction, month=1, victorious_faction=None)
    open_skirmish.attacking_warriors.add(committed_warrior)

    new_quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(quest_id=new_quest.id, player_faction_id=faction.id)

    assert list(form.fields["assigned_warriors"].queryset) == [committed_warrior]
    assert form.roster.reasons_by_warrior_id == {committed_warrior.id: REASON_STANDING_IN_AN_OPEN_FIGHT}


@pytest.mark.django_db
def test_assignable_warriors_leave_out_another_factions_warrior():
    """
    Widening the queryset to the whole war band is what lets the page draw the men who cannot go. The
    one thing it must go on doing is scoping to this faction, or a hand-edited id reaches a rival's
    man.
    """
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=FactionFactory(savegame=savegame))

    quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(quest_id=quest.id, player_faction_id=faction.id)

    assert list(form.fields["assigned_warriors"].queryset) == []


@pytest.mark.django_db
def test_help_text_stays_away_while_somebody_can_go():
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=faction)

    quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(quest_id=quest.id, player_faction_id=faction.id)

    assert form.fields["assigned_warriors"].help_text == ""


@pytest.mark.django_db
def test_help_text_says_when_every_row_is_greyed():
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(quest_id=quest.id, player_faction_id=faction.id)

    assert form.fields["assigned_warriors"].help_text == QuestAcceptForm.NOBODY_AVAILABLE


@pytest.mark.django_db
def test_clean_assigned_warriors_accepts_a_man_who_can_go():
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    warrior = WarriorFactory(faction=faction)

    quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(
        data={"faction": faction.id, "quest": quest.id, "assigned_warriors": [warrior.id]},
        quest_id=quest.id,
        player_faction_id=faction.id,
    )

    assert form.is_valid() is True
    assert list(form.cleaned_data["assigned_warriors"]) == [warrior]


@pytest.mark.django_db
def test_clean_assigned_warriors_refuses_a_man_who_cannot():
    """
    The queryset stopped being the gate the moment it had to hold the men who cannot go, and the
    "disabled" attribute only stops the browser. This is the rule.
    """
    savegame = SavegameFactory(current_month=2)
    faction = FactionFactory(savegame=savegame)
    unfit_warrior = WarriorFactory(
        faction=faction, name="Beorn", condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )

    quest = QuestFactory(target_faction__savegame=savegame)
    form = QuestAcceptForm(
        data={"faction": faction.id, "quest": quest.id, "assigned_warriors": [unfit_warrior.id]},
        quest_id=quest.id,
        player_faction_id=faction.id,
    )

    assert form.is_valid() is False
    assert form.errors["assigned_warriors"] == ["Beorn cannot take a quest this month."]
