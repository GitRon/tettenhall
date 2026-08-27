import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.services.generators.quest import QuestGenerator
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_process_targets_a_rival_faction():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=rival_faction)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.target_faction == rival_faction
    assert quest.loot > 0


@pytest.mark.django_db
def test_process_never_targets_a_defeated_faction():
    """
    A knocked-out faction is off the board, so the bulletin board must stop sending warbands after it.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame, is_defeated=True))
    rival_faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=rival_faction)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.target_faction == rival_faction


@pytest.mark.django_db
def test_process_never_targets_a_faction_that_fields_nobody():
    """
    The opposition is the rival's own war band now, so a flattened faction is not somewhere to send
    one - staging that fight raises on the empty side. Same rule the attack path already applies.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame), condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)
    rival_faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=rival_faction)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.target_faction == rival_faction


@pytest.mark.django_db
def test_process_without_a_rival_that_can_be_fought():
    """
    A quiet month rather than an exception: the month advance is what asks for a quest, and a player
    who has just beaten his last standing opponent has not broken the game.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame), condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest is None


@pytest.mark.django_db
def test_process_without_a_player_faction():
    savegame = SavegameFactory()

    with pytest.raises(RuntimeError, match="has no player faction to create a quest for"):
        QuestGenerator(savegame=savegame).process()


@pytest.mark.django_db
def test_process_without_a_rival_faction():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()

    with pytest.raises(RuntimeError, match="has no rival faction a quest could target"):
        QuestGenerator(savegame=savegame).process()
