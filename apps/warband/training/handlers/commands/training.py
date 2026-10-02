import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.calendar.months import get_calendar_month
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.training.messages.commands.training import ChangeTrainingRegimen, CreateNewTraining, TrainWarriors
from apps.warband.training.messages.events.training import (
    NewTrainingCreated,
    TrainingRegimenChanged,
    WarriorUpgradedSkill,
)
from apps.warband.training.models import Training


@message_registry.register_command(command=CreateNewTraining)
def handle_create_training_for_new_faction(*, context: CreateNewTraining) -> list[Event] | Event:
    training = Training.objects.create(
        category=random.choice(Training.TrainingCategory.choices)[0], faction=context.faction
    )

    return NewTrainingCreated(training=training)


@message_registry.register_command(command=ChangeTrainingRegimen)
def handle_change_training_regimen(*, context: ChangeTrainingRegimen) -> Event:
    context.training.category = context.category
    context.training.save(update_fields=["category"])

    return TrainingRegimenChanged(training=context.training)


@message_registry.register_command(command=TrainWarriors)
def handle_progress_warrior_training(*, context: TrainWarriors) -> list[Event] | Event:
    training = Training.objects.regimen_for_faction(faction_id=context.faction.id)

    # A faction without a training row has no regimen to train by. Every faction gets one from
    # NewFactionCreated on, so this is the savegame that predates the row rather than an ordinary month
    if training is None:
        return []

    training_category = training.category
    # Winter drills indoors, so the whole war band advances faster in the same month
    improvement_factor = get_calendar_month(month=context.month).TRAINING_FACTOR

    # Standing in a fight is not a state a warrior can be in while this runs: the advance is refused
    # outright when a skirmish is unresolved ("FinishMonthView"), and nothing the advance itself
    # raises creates one - the one path into a skirmish is a player click, marching on a rival. A man
    # who spent the month that ended away on a quest was not at the drill, so he is left out of it.
    warriors_to_train = context.faction.warriors.filter_healthy().exclude(
        id__in=Warrior.objects.filter_sworn_to_a_quest(month=context.month - 1).values("id")
    )

    event_list = []

    for warrior in warriors_to_train:
        attribute, improvement = training.get_random_attribute_and_improvement_for_category(
            category=training_category, improvement_factor=improvement_factor
        )

        attribute_progress_name = f"{attribute}_progress"
        new_value = getattr(warrior, attribute_progress_name) + improvement
        updated_fields = [attribute_progress_name]

        # Progress bar full -> skill upgrade
        if new_value >= 100:
            # "morale" and "health" grow their maximum, the others the attribute itself
            upgraded_attribute_name = f"max_{attribute}" if attribute in ("morale", "health") else attribute
            setattr(warrior, upgraded_attribute_name, getattr(warrior, upgraded_attribute_name) + 1)
            updated_fields.append(upgraded_attribute_name)

            # A finished course is growth, so a morale ceiling raised past the mark takes the mark along
            if attribute == "morale" and warrior.max_morale > warrior.peak_max_morale:
                warrior.peak_max_morale = warrior.max_morale
                updated_fields.append("peak_max_morale")

            # Reset progress bar after upgrade
            setattr(warrior, attribute_progress_name, 0)

            event_list.append(
                WarriorUpgradedSkill(
                    warrior=warrior,
                    training_category=training_category,
                    changed_attribute=attribute,
                    month=context.month,
                )
            )

        # Update on the progress bar
        else:
            setattr(warrior, attribute_progress_name, new_value)

        # Only the fields touched above: a full save would write back everything else this instance
        # still holds from before
        warrior.save(update_fields=updated_fields)

    return event_list
