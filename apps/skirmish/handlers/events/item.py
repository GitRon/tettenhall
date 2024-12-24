from apps.core.domain import message_registry
from apps.item.models.item import Item
from apps.skirmish.messages.commands.item import WarriorDropsLoot
from apps.skirmish.messages.commands.transaction import WarriorDropsSilver
from apps.skirmish.messages.events import item, skirmish
from apps.skirmish.models.warrior import Warrior


@message_registry.register_event(event=skirmish.SkirmishFinished)
def handle_distribute_loot(*, context: skirmish.SkirmishFinished.Context):
    message_list = []

    # The winner drops only items from dead warriors, the loser from all dead or incapacitated
    if context.skirmish.victorious_faction == context.skirmish.player_faction:
        winner_warrior_list = context.skirmish.player_warriors.filter(condition=Warrior.ConditionChoices.CONDITION_DEAD)
        loser_warrior_list = context.skirmish.non_player_warriors.filter(
            condition__in=[Warrior.ConditionChoices.CONDITION_UNCONSCIOUS, Warrior.ConditionChoices.CONDITION_DEAD]
        )
    else:
        winner_warrior_list = context.skirmish.non_player_warriors.filter(
            condition=Warrior.ConditionChoices.CONDITION_DEAD
        )
        loser_warrior_list = context.skirmish.player_warriors.filter(
            condition__in=[Warrior.ConditionChoices.CONDITION_UNCONSCIOUS, Warrior.ConditionChoices.CONDITION_DEAD]
        )

    warriors_dropping_loot_list = [*winner_warrior_list, *loser_warrior_list]

    for warrior in warriors_dropping_loot_list:
        message_list.append(
            WarriorDropsLoot(
                WarriorDropsLoot.Context(
                    skirmish=context.skirmish,
                    warrior=warrior,
                    new_owner=context.skirmish.victorious_faction,
                )
            )
        )
        message_list.append(
            WarriorDropsSilver(
                WarriorDropsSilver.Context(
                    skirmish=context.skirmish,
                    warrior=warrior,
                    gaining_faction=context.skirmish.victorious_faction,
                )
            )
        )

    return message_list


@message_registry.register_event(event=item.ItemDroppedAsLoot)
def handle_looted_item_changes_ownership(*, context: item.ItemDroppedAsLoot.Context):
    # Take item away from previous owner
    Warrior.objects.take_item_away(item=context.item)

    # Set ownership in the item itself so it belongs to the winning faction
    Item.objects.update_ownership(item=context.item, new_owner=context.new_owner)
