from apps.faction.tests.factories.faction import FactionFactory
from apps.month.messages.commands.month import CreatePlayerMonthLog
from apps.month.messages.events.month import PlayerMonthPrepared
from apps.savegame.tests.factories.savegame import SavegameFactory
from apps.skirmish.tests.factories.warrior import WarriorFactory
from apps.training.handlers.events.training import (
    handle_training_of_warriors_for_new_month,
    handle_warrior_upgraded_skill,
)
from apps.training.messages.commands.training import TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill
from apps.training.models import Training
from apps.training.tests.factories.training import TrainingFactory


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

    assert result == CreatePlayerMonthLog(title="Your warrior Beorn upgraded his strength!", month=3, faction=faction)


def test_handle_training_of_warriors_for_new_month_requests_the_training():
    faction = FactionFactory.build()
    savegame = SavegameFactory.build()
    training = TrainingFactory.build(faction=faction)

    result = handle_training_of_warriors_for_new_month(
        context=PlayerMonthPrepared(faction=faction, savegame=savegame, training=training, current_month=3)
    )

    assert result == [TrainWarriors(faction=faction, training=training, month=3)]


def test_handle_training_of_warriors_for_new_month_without_a_training():
    """
    A player faction without a training row has nothing to train, and the command handler
    dereferences "training" unguarded - so finishing the month would answer with a 500.
    """
    faction = FactionFactory.build()
    savegame = SavegameFactory.build()

    result = handle_training_of_warriors_for_new_month(
        context=PlayerMonthPrepared(faction=faction, savegame=savegame, training=None, current_month=3)
    )

    assert result == []
