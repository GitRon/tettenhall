import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.quest.models.quest import Quest
from apps.quest.tests.factories.quest import QuestFactory
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.models.warrior import Warrior
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
    A quest outlives the month it was offered in, so the faction it names may have been flattened
    since - and the opposition is that faction's own war band now, so accepting one then stages a
    fight against an empty side.
    """
    savegame = SavegameFactory()
    fightable_quest = QuestFactory(target_faction__savegame=savegame)
    WarriorFactory(faction=fightable_quest.target_faction)
    flattened_quest = QuestFactory(target_faction__savegame=savegame)
    WarriorFactory(faction=flattened_quest.target_faction, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS)

    assert list(Quest.objects.resolvable()) == [fightable_quest]


@pytest.mark.django_db
def test_resolvable_lists_a_quest_once_per_target_no_matter_its_war_band():
    """
    The filter joins the target's roster, so without the "distinct" a faction with three men on its
    feet would hand the same quest back three times.
    """
    quest = QuestFactory()
    WarriorFactory(faction=quest.target_faction)
    WarriorFactory(faction=quest.target_faction)

    assert list(Quest.objects.resolvable()) == [quest]
