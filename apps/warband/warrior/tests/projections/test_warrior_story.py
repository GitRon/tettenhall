import pytest

from apps.warband.calendar.date import CalendarDate
from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.quest.tests.factories.quest_contract import QuestContractFactory
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.skirmish_casualty import SkirmishCasualty
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.tests.factories.skirmish import SkirmishFactory
from apps.warband.skirmish.tests.factories.skirmish_casualty import SkirmishCasualtyFactory
from apps.warband.skirmish.tests.factories.skirmish_warrior_growth import SkirmishWarriorGrowthFactory
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.warrior_milestone import JoinedWayChoices, MilestoneKindChoices
from apps.warband.warrior.projections.warrior_story import (
    CHANGED_WORDING,
    STORY_LENGTH,
    StoryEntry,
    WarriorStory,
    describe_milestone,
    describe_naming_reason,
    join_names,
)
from apps.warband.warrior.services.nickname import GIANTBANE_NICKNAMES, STRENGTH_NICKNAMES
from apps.warband.warrior.tests.factories.injury import InjuryFactory
from apps.warband.warrior.tests.factories.injury_type import InjuryTypeFactory
from apps.warband.warrior.tests.factories.warrior_milestone import WarriorMilestoneFactory


def _date(*, warrior: Warrior, month: int) -> CalendarDate:
    return CalendarDate.for_month(month=month, start_year=warrior.savegame.start_year)


def _fight(*, warrior: Warrior, month: int, attacking: bool = True, won: bool = True, **kwargs) -> Skirmish:
    """A fight he stood in and that has been decided, on the side his own faction took."""
    if attacking:
        skirmish = SkirmishFactory(attacking_faction=warrior.faction, month=month, **kwargs)
        skirmish.attacking_warriors.add(warrior)
    else:
        skirmish = SkirmishFactory(
            defending_faction=warrior.faction,
            attacking_faction__savegame=warrior.savegame,
            month=month,
            **kwargs,
        )
        skirmish.defending_warriors.add(warrior)

    own_side = warrior.faction
    other_side = skirmish.defending_faction if attacking else skirmish.attacking_faction
    Skirmish.objects.set_victor(skirmish=skirmish, victorious_faction=own_side if won else other_side)
    skirmish.refresh_from_db()

    return skirmish


@pytest.mark.django_db
def test_for_warrior_tells_nothing_of_a_man_with_no_history():
    warrior = WarriorFactory()

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == []


@pytest.mark.django_db
def test_for_warrior_tells_a_fight_he_won_with_how_it_ended_whom_he_killed_and_what_it_made_of_him():
    warrior = WarriorFactory(faction__name="Mercia", nickname_variant=0)
    skirmish = _fight(warrior=warrior, month=3, defending_faction__name="Wessex")
    SkirmishCasualtyFactory(skirmish=skirmish, warrior=warrior, fate=SkirmishCasualty.FateChoices.FATE_INCAPACITATED)
    SkirmishCasualtyFactory(skirmish=skirmish, warrior__name="Oswy", killed_by=warrior)
    SkirmishCasualtyFactory(skirmish=skirmish, warrior__name="Eadric", killed_by=warrior)
    SkirmishWarriorGrowthFactory(skirmish=skirmish, warrior=warrior, reached_level=3)
    giant = WarriorFactory(name="Oswy")
    WarriorMilestoneFactory(
        warrior=warrior,
        kind=MilestoneKindChoices.NAMED,
        month=3,
        skirmish=skirmish,
        other_warrior=giant,
        nickname_state=NicknameStateChoices.GIANTBANE,
        joined_way=None,
    )
    WarriorMilestoneFactory(
        warrior=warrior, kind=MilestoneKindChoices.CHANGED, month=3, skirmish=skirmish, joined_way=None
    )

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == [
        StoryEntry(
            when=_date(warrior=warrior, month=3),
            headline="Fought for Mercia against Wessex, and won",
            details=(
                "Knocked unconscious",
                "Killed Oswy and Eadric",
                "Reached level 3",
                f"Came to be called {GIANTBANE_NICKNAMES[0]} for felling Oswy, a man far above him",
                CHANGED_WORDING,
            ),
            order=(3, 2, skirmish.id),
        )
    ]


@pytest.mark.django_db
def test_for_warrior_tells_a_fight_he_lost_defending():
    warrior = WarriorFactory(faction__name="Mercia")
    skirmish = _fight(warrior=warrior, month=4, attacking=False, won=False, attacking_faction__name="Wessex")

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert [(entry.headline, entry.order) for entry in result.entries] == [
        ("Fought for Mercia against Wessex, and lost", (4, 2, skirmish.id))
    ]


@pytest.mark.django_db
def test_for_warrior_leaves_out_a_fight_still_being_fought():
    warrior = WarriorFactory()
    SkirmishFactory(attacking_faction=warrior.faction).attacking_warriors.add(warrior)

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == []


@pytest.mark.django_db
def test_for_warrior_leaves_out_a_change_the_viewer_did_not_see():
    """
    He changed while he stood under another banner than the viewer's, so the viewer was not there to
    see it - see docs/patterns/warrior-knowledge.md.
    """
    warrior = WarriorFactory()
    WarriorMilestoneFactory(warrior=warrior, kind=MilestoneKindChoices.CHANGED, month=2, joined_way=None)
    viewer = FactionFactory(savegame=warrior.savegame)

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=viewer.id)

    assert result.entries == []


@pytest.mark.django_db
def test_for_warrior_tells_a_change_the_viewer_saw_outside_any_fight_on_the_page():
    warrior = WarriorFactory()
    milestone = WarriorMilestoneFactory(warrior=warrior, kind=MilestoneKindChoices.CHANGED, month=2, joined_way=None)

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == [
        StoryEntry(when=_date(warrior=warrior, month=2), headline=CHANGED_WORDING, order=(2, 4, milestone.id))
    ]


@pytest.mark.django_db
def test_for_warrior_tells_how_he_joined_before_what_he_did_that_month():
    warrior = WarriorFactory(faction__name="Mercia", nickname_variant=0)
    named = WarriorMilestoneFactory(
        warrior=warrior,
        kind=MilestoneKindChoices.NAMED,
        month=1,
        nickname_state=NicknameStateChoices.STRENGTH,
        joined_way=None,
    )
    joined = WarriorMilestoneFactory(warrior=warrior, month=1, joined_way=JoinedWayChoices.HIRED)

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=None)

    assert [(entry.headline, entry.order) for entry in result.entries] == [
        (f"Came to be called {STRENGTH_NICKNAMES[0]}", (1, 4, named.id)),
        ("Hired from the pub by Mercia", (1, 0, joined.id)),
    ]


@pytest.mark.django_db
def test_for_warrior_tells_an_errand_still_away():
    warrior = WarriorFactory()
    contract = QuestContractFactory(
        faction=warrior.faction, title="Drive off the wolves", accepted_in_month=5, assigned_warriors=[warrior]
    )

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == [
        StoryEntry(
            when=_date(warrior=warrior, month=5),
            headline="Sent on an errand: Drive off the wolves",
            order=(5, 1, contract.id),
        )
    ]


@pytest.mark.django_db
def test_for_warrior_tells_when_he_came_home_from_an_errand():
    warrior = WarriorFactory()
    QuestContractFactory(faction=warrior.faction, accepted_in_month=5, resolved_in_month=6, assigned_warriors=[warrior])

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries[0].details == (f"Came home {_date(warrior=warrior, month=6).label}",)


@pytest.mark.django_db
def test_for_warrior_tells_a_lasting_wound():
    warrior = WarriorFactory()
    injury = InjuryFactory(
        warrior=warrior,
        type=InjuryTypeFactory(name="Stiff ankle", attribute="dexterity", magnitude=1),
        inflicted_in_month=7,
    )

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert result.entries == [
        StoryEntry(
            when=_date(warrior=warrior, month=7),
            headline="Marked for good: Stiff ankle (-1 Dexterity)",
            order=(7, 3, injury.id),
        )
    ]


@pytest.mark.django_db
def test_for_warrior_tells_only_the_latest_entries_newest_first():
    warrior = WarriorFactory()
    for month in range(1, STORY_LENGTH + 3):
        WarriorMilestoneFactory(warrior=warrior, month=month)

    result = WarriorStory.for_warrior(warrior=warrior, viewer_faction_id=warrior.faction_id)

    assert [entry.order[0] for entry in result.entries] == list(range(STORY_LENGTH + 2, 2, -1))


def test_describe_milestone_for_a_man_who_joined():
    milestone = WarriorMilestoneFactory.build(
        faction=FactionFactory.build(name="Mercia"), joined_way=JoinedWayChoices.SWORN_FROM_CELLS
    )

    result = describe_milestone(milestone=milestone, nickname_variant=0)

    assert result == "Sworn in from the cells of Mercia"


def test_describe_milestone_for_a_seat_taken_from_a_man_on_record():
    milestone = WarriorMilestoneFactory.build(
        kind=MilestoneKindChoices.TOOK_SEAT,
        faction=FactionFactory.build(name="Mercia"),
        other_warrior=WarriorFactory.build(name="Offa"),
    )

    result = describe_milestone(milestone=milestone, nickname_variant=0)

    assert result == "Took the seat of Offa at the head of Mercia"


def test_describe_milestone_for_a_seat_taken_from_a_man_no_longer_on_record():
    milestone = WarriorMilestoneFactory.build(
        kind=MilestoneKindChoices.TOOK_SEAT, faction=FactionFactory.build(name="Mercia"), other_warrior=None
    )

    result = describe_milestone(milestone=milestone, nickname_variant=0)

    assert result == "Took the seat at the head of Mercia"


def test_describe_milestone_for_a_deed_names_the_reason():
    milestone = WarriorMilestoneFactory.build(
        kind=MilestoneKindChoices.NAMED, nickname_state=NicknameStateChoices.WALLBREAKER
    )

    result = describe_milestone(milestone=milestone, nickname_variant=0)

    assert result.endswith("for the swing that brought the walls down")


def test_describe_naming_reason_for_a_lord_slain():
    result = describe_naming_reason(
        nickname_state=NicknameStateChoices.LORD_SLAYER, other_warrior=WarriorFactory.build(name="Offa")
    )

    assert result == "for the blow that killed Offa"


def test_describe_naming_reason_for_a_lord_no_longer_on_record():
    result = describe_naming_reason(nickname_state=NicknameStateChoices.LORD_SLAYER, other_warrior=None)

    assert result == "for the blow that killed a lord"


def test_describe_naming_reason_for_a_giant_no_longer_on_record():
    result = describe_naming_reason(nickname_state=NicknameStateChoices.GIANTBANE, other_warrior=None)

    assert result == "for felling a man far above him"


def test_describe_naming_reason_for_an_epithet_he_was_drawn_with():
    result = describe_naming_reason(nickname_state=NicknameStateChoices.STRENGTH_FAR, other_warrior=None)

    assert result is None


def test_join_names_for_one_man():
    assert join_names(names=["Oswy"]) == "Oswy"


def test_join_names_for_three_men():
    assert join_names(names=["Oswy", "Eadric", "Wulf"]) == "Oswy, Eadric and Wulf"
