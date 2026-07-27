from apps.skirmish.choices.skirmish_action import SkirmishActionChoices
from apps.skirmish.projections.skirmish_participant import SkirmishParticipant
from apps.skirmish.services.skirmish.assign_fighter_pairs import AssignFighterPairsService
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_determine_larger_group_starts_with_the_first_group():
    first_group = [
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK),
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK),
    ]
    second_group = [
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK)
    ]

    result = AssignFighterPairsService.determine_larger_group(
        skirmish_participants_1=first_group, skirmish_participants_2=second_group
    )

    assert result == (first_group, second_group)


def test_determine_larger_group_starts_with_the_second_group():
    first_group = [
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK)
    ]
    second_group = [
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK),
        SkirmishParticipant(warrior=WarriorFactory.build(), skirmish_action=SkirmishActionChoices.SIMPLE_ATTACK),
    ]

    result = AssignFighterPairsService.determine_larger_group(
        skirmish_participants_1=first_group, skirmish_participants_2=second_group
    )

    assert result == (second_group, first_group)
