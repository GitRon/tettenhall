from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.training.messages.events.training import WarriorUpgradedSkill
from apps.warband.training.models import Training
from apps.warband.warrior.handlers.events.training import handle_training_earns_a_nickname
from apps.warband.warrior.messages.commands.warrior import AwardEarnedNickname


def test_handle_training_earns_a_nickname_asks_on_every_upgrade():
    warrior = WarriorFactory.build()

    result = handle_training_earns_a_nickname(
        context=WarriorUpgradedSkill(
            warrior=warrior,
            training_category=Training.TrainingCategory.WEAPON_MASTERY,
            changed_attribute="strength",
            month=3,
        )
    )

    assert result == AwardEarnedNickname(warrior=warrior, month=3)
