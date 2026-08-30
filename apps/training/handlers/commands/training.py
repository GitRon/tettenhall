import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.training.messages.commands.training import CreateNewTraining, TrainWarriors
from apps.training.messages.events.training import NewTrainingCreated, WarriorUpgradedSkill
from apps.training.models import Training


@message_registry.register_command(command=CreateNewTraining)
def handle_create_training_for_new_faction(*, context: CreateNewTraining) -> list[Event] | Event:
    training = Training.objects.create(
        category=random.choice(Training.TrainingCategory.choices)[0], faction=context.faction
    )

    return NewTrainingCreated(training=training)


@message_registry.register_command(command=TrainWarriors)
def handle_progress_warrior_training(*, context: TrainWarriors) -> list[Event] | Event:
    training_category = context.training.category
    warriors_to_train = context.faction.warriors.filter_healthy()

    event_list = []

    for warrior in warriors_to_train:
        attribute, improvement = context.training.get_random_attribute_and_improvement_for_category(
            category=training_category
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
