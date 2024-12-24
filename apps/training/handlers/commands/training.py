from apps.core.domain import message_registry
from apps.core.event_loop.messages import Event
from apps.skirmish.models.warrior import Warrior
from apps.training.messages.commands.training import TrainWarriors
from apps.training.messages.events.training import WarriorUpgradedSkill


@message_registry.register_command(command=TrainWarriors)
def handle_replenish_fyrd_reserve(*, context: TrainWarriors.Context) -> list[Event] | Event:
    training_category = context.training.category
    warriors_to_train = context.faction.warriors.filter(condition=Warrior.ConditionChoices.CONDITION_HEALTHY)

    event_list = []

    for warrior in warriors_to_train:
        attribute, improvement = context.training.get_random_attribute_and_improvement_for_category(
            category=training_category
        )

        if improvement <= 0:
            continue

        attribute_progress_name = f"{attribute}_progress"
        current_value = getattr(warrior, attribute_progress_name)
        new_value = current_value + improvement
        # Progress bar full -> skill upgrade
        if new_value >= 100:
            new_value = 0
            if attribute in ("morale", "health"):
                max_attribute_name = f"max_{attribute}"
                current_max_value = getattr(warrior, max_attribute_name)
                setattr(warrior, max_attribute_name, current_max_value + 1)
            else:
                current_max_value = getattr(warrior, attribute)
                setattr(warrior, attribute, current_max_value + 1)

            # Reset progress bar after upgrade
            setattr(warrior, attribute_progress_name, 0)

            event_list.append(
                WarriorUpgradedSkill(
                    WarriorUpgradedSkill.Context(
                        warrior=warrior,
                        training_category=training_category,
                        changed_attribute=attribute,
                        week=context.week,
                    )
                )
            )

        # Update on the progress bar
        else:
            setattr(warrior, attribute_progress_name, current_value + improvement)

        warrior.save()

    return event_list
