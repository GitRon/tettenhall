import pytest

from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.choices.posting import PostingChoices
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.raids.kinds import BurnTheVillage, LiftTheHerds, StormTheBurh
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.services.availability import REASON_SWORN_TO_A_QUEST
from apps.warband.warrior.services.postings import (
    RAID_KIND_BY_POSTING,
    PostingColumn,
    count_men_standing,
    get_posting_columns,
)


@pytest.mark.django_db
def test_count_men_standing_counts_only_the_men_a_raid_would_meet_there_today():
    """
    The man who is down and the man away on a quest keep their posting, and are not there to stand. The
    burh counts every man at home, because its assault meets all of them.
    """
    faction = FactionFactory()
    WarriorFactory(faction=faction, posting=PostingChoices.HERDS)
    WarriorFactory(
        faction=faction, posting=PostingChoices.HERDS, condition=Warrior.ConditionChoices.CONDITION_UNCONSCIOUS
    )
    WarriorFactory(faction=faction, posting=PostingChoices.VILLAGE)
    QuestContractFactory(
        faction=faction,
        accepted_in_month=3,
        assigned_warriors=[WarriorFactory(faction=faction, posting=PostingChoices.VILLAGE)],
    )
    WarriorFactory(faction=FactionFactory(), posting=PostingChoices.BURH)

    places = count_men_standing(faction_id=faction.id, month=3)

    assert [(place.label, place.standing_count) for place in places] == [("Burh", 2), ("Village", 1), ("Herds", 1)]


@pytest.mark.django_db
def test_get_posting_columns_draws_every_living_man_at_his_place_with_the_reason_he_is_not_there():
    faction = FactionFactory()
    herdsman = WarriorFactory(faction=faction, posting=PostingChoices.HERDS, name="Aelfric")
    away = WarriorFactory(faction=faction, posting=PostingChoices.HERDS, name="Beorn")
    QuestContractFactory(faction=faction, accepted_in_month=3, assigned_warriors=[away])
    WarriorFactory(faction=faction, condition=Warrior.ConditionChoices.CONDITION_DEAD)

    columns = get_posting_columns(faction_id=faction.id, month=3)

    assert [
        (column.raid_kind, [(man.warrior, man.reason) for man in column.men], column.standing_count)
        for column in columns
    ] == [
        (StormTheBurh, [], 1),
        (BurnTheVillage, [], 0),
        (LiftTheHerds, [(herdsman, None), (away, REASON_SWORN_TO_A_QUEST)], 1),
    ]


@pytest.mark.django_db
def test_get_posting_columns_brings_the_faction_along_for_the_names(django_assert_num_queries):
    """The board names every man in full, which asks his faction whether he holds its seat."""
    faction = FactionFactory()
    WarriorFactory.create_batch(3, faction=faction)
    columns = get_posting_columns(faction_id=faction.id, month=3)

    with django_assert_num_queries(0):
        names = [man.warrior.display_name for column in columns for man in column.men]

    assert len(names) == 3


def test_posting_column_offers_the_two_other_places():
    column = PostingColumn(
        posting=PostingChoices.VILLAGE,
        label="Village",
        raid_kind=RAID_KIND_BY_POSTING[PostingChoices.VILLAGE],
        men=[],
        standing_count=0,
    )

    assert column.other_postings == [(PostingChoices.BURH, "Burh"), (PostingChoices.HERDS, "Herds")]
