import pytest

from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.choices.nickname import NicknameStateChoices
from apps.warband.warrior.choices.warrior_milestone import MilestoneKindChoices
from apps.warband.warrior.models.warrior_milestone import WarriorMilestone
from apps.warband.warrior.tests.factories.warrior_milestone import WarriorMilestoneFactory


@pytest.mark.django_db
def test_str_names_the_man_and_the_moment():
    milestone = WarriorMilestoneFactory(warrior__name="Cuthred")

    assert str(milestone) == "Cuthred: Joined a war band"


@pytest.mark.django_db
def test_create_record_writes_the_row():
    warrior = WarriorFactory()

    milestone = WarriorMilestone.objects.create_record(
        warrior=warrior,
        kind=MilestoneKindChoices.NAMED,
        month=5,
        faction=warrior.faction,
        nickname_state=NicknameStateChoices.UNBROKEN,
    )

    assert list(warrior.milestones.all()) == [milestone]


@pytest.mark.django_db
def test_for_warrior_narrows_to_one_man():
    milestone = WarriorMilestoneFactory()
    WarriorMilestoneFactory()

    result = WarriorMilestone.objects.for_warrior(warrior_id=milestone.warrior_id)

    assert list(result) == [milestone]
