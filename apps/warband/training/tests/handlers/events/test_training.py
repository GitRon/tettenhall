from apps.warband.faction.tests.factories.faction import FactionFactory
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.messages.events.month import FactionMonthPrepared
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.training.handlers.events.training import (
    handle_training_of_warriors_for_new_month,
    handle_warrior_upgraded_skill,
)
from apps.warband.training.messages.commands.training import TrainWarriors
from apps.warband.training.messages.events.training import WarriorUpgradedSkill
from apps.warband.training.models import Training


def test_handle_warrior_upgraded_skill_logs_the_upgraded_attribute():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_warrior_upgraded_skill(
        context=WarriorUpgradedSkill(
            warrior=warrior,
            training_category=Training.TrainingCategory.WEAPON_MASTERY,
            changed_attribute="strength",
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(
        title="Your warrior Beorn upgraded his strength!",
        kind=PlayerMonthLog.KindChoices.KIND_SKILL_UPGRADE,
        month=3,
        faction=faction,
    )


def test_handle_training_of_warriors_for_new_month_requests_the_training():
    """
    Pure mapping handler: the regimen is looked up in the command handler, so this one only reads
    from the message and built instances are enough.
    """
    faction = FactionFactory.build()

    result = handle_training_of_warriors_for_new_month(context=FactionMonthPrepared(faction=faction, current_month=3))

    assert result == [TrainWarriors(faction=faction, month=3)]
