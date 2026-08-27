from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.handlers.commands.quest import handle_accept_quest, handle_create_new_quest
from apps.quest.messages.commands.quest import AcceptQuest, CreateNewQuest
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_handle_create_new_quest_pins_a_quest_to_the_board():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame))

    result = handle_create_new_quest(
        context=CreateNewQuest(savegame=savegame, faction=savegame.player_faction, month=3)
    )

    assert result.quest == Quest.objects.get()
    assert list(savegame.player_faction.available_quests.all()) == [result.quest]


@pytest.mark.django_db
def test_handle_create_new_quest_offers_nothing_when_every_rival_is_flattened():
    """
    A quiet month rather than an error: the month advance is what asks for a quest, and a player who
    has just beaten his last standing opponent has not broken the game.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame), condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    result = handle_create_new_quest(
        context=CreateNewQuest(savegame=savegame, faction=savegame.player_faction, month=3)
    )

    assert result is None
    assert Quest.objects.exists() is False


@pytest.mark.django_db
def test_handle_accept_quest_signs_the_contract():
    quest = QuestFactory()
    accepting_faction = FactionFactory(savegame=quest.target_faction.savegame)
    warrior = WarriorFactory(faction=accepting_faction)
    accepting_faction.available_quests.add(quest)
    WarriorFactory(faction=quest.target_faction)

    result = handle_accept_quest(
        context=AcceptQuest(accepting_faction=accepting_faction, quest=quest, assigned_warriors=[warrior], month=3)
    )

    assert result.quest_contract == QuestContract.objects.get()
    assert list(accepting_faction.available_quests.all()) == []


@pytest.mark.django_db
def test_handle_accept_quest_musters_as_many_defenders_as_the_difficulty_asks_for():
    quest = QuestFactory(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD)
    accepting_faction = FactionFactory(savegame=quest.target_faction.savegame)
    for _ in range(6):
        WarriorFactory(faction=quest.target_faction)

    # Boundary randomness: how many of them turn out is a random draw within the difficulty band
    with mock.patch("apps.quest.handlers.commands.quest.random.randint", return_value=4):
        result = handle_accept_quest(
            context=AcceptQuest(
                accepting_faction=accepting_faction,
                quest=quest,
                assigned_warriors=[WarriorFactory(faction=accepting_faction)],
                month=3,
            )
        )

    assert len(result.target_warriors) == 4


@pytest.mark.django_db
def test_handle_accept_quest_musters_no_more_defenders_than_the_target_has():
    """
    The difficulty is a selection size, not a spawn count: a faction with fewer men than the band
    asks for fields what it has, and the payout scales down with it.
    """
    quest = QuestFactory(difficulty=Quest.DifficultyChoices.DIFFICULTY_HARD)
    accepting_faction = FactionFactory(savegame=quest.target_faction.savegame)
    defender = WarriorFactory(faction=quest.target_faction)

    with mock.patch("apps.quest.handlers.commands.quest.random.randint", return_value=7):
        result = handle_accept_quest(
            context=AcceptQuest(
                accepting_faction=accepting_faction,
                quest=quest,
                assigned_warriors=[WarriorFactory(faction=accepting_faction)],
                month=3,
            )
        )

    assert result.target_warriors == [defender]


@pytest.mark.django_db
def test_handle_accept_quest_leaves_the_targets_casualties_at_home():
    """
    A warrior who is down does not defend his town, and a side made up of him alone would count as
    beaten before the first round.
    """
    quest = QuestFactory()
    accepting_faction = FactionFactory(savegame=quest.target_faction.savegame)
    healthy_defender = WarriorFactory(faction=quest.target_faction)
    WarriorFactory(faction=quest.target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    with mock.patch("apps.quest.handlers.commands.quest.random.randint", return_value=5):
        result = handle_accept_quest(
            context=AcceptQuest(
                accepting_faction=accepting_faction,
                quest=quest,
                assigned_warriors=[WarriorFactory(faction=accepting_faction)],
                month=3,
            )
        )

    assert result.target_warriors == [healthy_defender]
