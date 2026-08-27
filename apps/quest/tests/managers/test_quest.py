import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest import Quest
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
from apps.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory


@pytest.mark.django_db
def test_for_player_faction_keeps_only_what_is_on_that_bulletin_board():
    """
    Every faction of a savegame gets its own quests offered, so the savegame is the wrong scope for
    singling out what the player was actually offered.
    """
    savegame = SavegameFactory()
    player_faction = FactionFactory(savegame=savegame)
    rival_faction = FactionFactory(savegame=savegame)

    offered_quest = QuestFactory(target_faction__savegame=savegame)
    player_faction.available_quests.add(offered_quest)
    rival_quest = QuestFactory(target_faction__savegame=savegame)
    rival_faction.available_quests.add(rival_quest)
    # In the savegame, but pinned to nobody's board
    QuestFactory(target_faction__savegame=savegame)

    assert list(Quest.objects.for_player_faction(faction_id=player_faction.id)) == [offered_quest]


@pytest.mark.django_db
def test_resolvable_keeps_only_quests_whose_target_still_fields_somebody():
    """
    The card can go stale inside the month it was offered in: the opposition is that faction's own war
    band now, so accepting one whose men are all down would stage a fight against an empty side.
    """
    savegame = SavegameFactory()
    fightable_quest = QuestFactory(target_faction__savegame=savegame)
    WarriorFactory(faction=fightable_quest.target_faction)
    flattened_quest = QuestFactory(target_faction__savegame=savegame)
    WarriorFactory(faction=flattened_quest.target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    assert list(Quest.objects.resolvable(month=1)) == [fightable_quest]


@pytest.mark.django_db
def test_resolvable_lists_a_quest_once_per_target_no_matter_its_war_band():
    """
    The target is matched through a subquery on the warrior rather than a join on the roster, so a
    faction with several men on its feet still hands the quest back once.
    """
    quest = QuestFactory()
    WarriorFactory(faction=quest.target_faction)
    WarriorFactory(faction=quest.target_faction)

    assert list(Quest.objects.resolvable(month=1)) == [quest]


@pytest.mark.django_db
def test_resolvable_drops_a_target_that_has_been_knocked_out():
    """
    Matching [FactionQuerySet.attackable_targets], which a defeated faction never passes. Reachable
    because the muster is a subset of the roster: a faction can lose its leader among the men it
    fielded and still have somebody healthy at home.
    """
    quest = QuestFactory(target_faction__is_defeated=True)
    WarriorFactory(faction=quest.target_faction)

    assert list(Quest.objects.resolvable(month=1)) == []


@pytest.mark.django_db
def test_resolvable_drops_a_target_whose_defenders_are_already_in_a_fight():
    """
    Every warrior fights once a month, defenders included. A man mustered onto two open skirmishes
    strands whichever is resolved second - the side that lost him cannot be played out, and the month
    refuses to turn while a skirmish is open.
    """
    quest = QuestFactory()
    committed_defender = WarriorFactory(faction=quest.target_faction)
    SkirmishFactory(defending_faction=quest.target_faction).defending_warriors.add(committed_defender)

    assert list(Quest.objects.resolvable(month=1)) == []
