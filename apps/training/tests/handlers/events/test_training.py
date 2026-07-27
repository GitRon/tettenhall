from apps.faction.tests.factories.faction import FactionFactory
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.training.handlers.events.training import handle_pub_mercenaries_restocked
from apps.training.messages.events.training import WarriorUpgradedSkill
from apps.training.models import Training


def test_handle_pub_mercenaries_restocked_logs_the_upgraded_attribute():
    faction = FactionFactory.build()
    warrior = WarriorFactory.build(name="Beorn", faction=faction)

    result = handle_pub_mercenaries_restocked(
        context=WarriorUpgradedSkill(
            warrior=warrior,
            training_category=Training.TrainingCategory.WEAPON_MASTERY,
            changed_attribute="strength",
            month=3,
        )
    )

    assert result == CreatePlayerMonthLog(title="Your warrior Beorn upgraded his strength!", month=3, faction=faction)
