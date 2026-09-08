from unittest import mock

import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest_name import QuestName
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
def test_process_prices_a_quest_against_a_roster_below_the_band():
    """
    A rival opens a savegame with a single warrior and gains at most one a month, so for the first
    several months neither band's top can turn out. The contract is written for the war band there
    is, and both bands start above two.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)
    WarriorFactory.create_batch(2, faction=rival_faction)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.expected_opposition == 2


@pytest.mark.django_db
def test_process_prices_a_quest_at_full_price_for_a_roster_past_the_band():
    """
    A target with more men than the difficulty musters is the case the band tops were written for,
    and it signs the contract at its face value.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    rival_faction = FactionFactory(savegame=savegame)
    # Past the top of either band, so the difficulty the generator rolls cannot change the answer
    WarriorFactory.create_batch(9, faction=rival_faction)

    # Patched at the boundary: the loot roll
    with mock.patch("apps.quest.models.quest.random.randint", return_value=300):
        quest = QuestGenerator(savegame=savegame).process()

    assert quest.expected_opposition == quest.get_min_max_number_of_opponents()[1]
    assert quest.loot == 300


@pytest.mark.django_db
def test_process_prices_a_quest_against_the_men_who_could_turn_out():
    """
    The same muster "_muster_defenders" will run on the day: a warrior who is down does not defend
    his town, and the player's own war band is not the opposition.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory.create_batch(3, faction=savegame.player_faction)
    rival_faction = FactionFactory(savegame=savegame)
    WarriorFactory(faction=rival_faction)
    WarriorFactory.create_batch(2, faction=rival_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.expected_opposition == 1


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


@pytest.mark.django_db
def test_process_names_a_quest_from_the_reference_data():
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame))

    quest = QuestGenerator(savegame=savegame).process()

    assert quest.name in QuestName.objects.values_list("name", flat=True)


@pytest.mark.django_db
def test_process_without_quest_names():
    """
    A half-seeded database rather than a savegame that ran out of errands, so it is named as one.
    """
    savegame = SavegameFactory()
    savegame.player_faction = FactionFactory(savegame=savegame)
    savegame.save()
    WarriorFactory(faction=FactionFactory(savegame=savegame))
    QuestName.objects.all().delete()

    with pytest.raises(RuntimeError, match="no quest names to draw from"):
        QuestGenerator(savegame=savegame).process()
