from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.town.messages.events.town import FeastThrown, GeldCalled


@message_registry.register_event(event=FeastThrown)
def handle_feast_thrown(*, context: FeastThrown) -> Command:
    """
    One line for the whole table: what it cost, and how many it actually helped.

    The second number is the one the player paid to learn. A feast charges for every man and mends
    only the cut ones, so a line that named the bill alone would read the same for a war band that
    needed it and one that did not.
    """
    fed = len(context.warrior_list)
    mended = sum(1 for warrior in context.warrior_list if warrior.is_mended_by_a_feast)
    hall_name = context.town.get_building_level_display(building_type="hall", level=context.town.hall)

    title = f"A feast in the {hall_name} fed {fed} {'man' if fed == 1 else 'men'} for {context.costs} silver"
    title += f" and mended the nerve of {mended}." if mended else "."

    return CreatePlayerMonthLog(
        title=title,
        kind=PlayerMonthLog.KindChoices.KIND_FEAST_THROWN,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=GeldCalled)
def handle_geld_called(*, context: GeldCalled) -> Command:
    """
    Both halves of the trade on one line, because the second is the one easy to forget: the silver shows
    in the purse, a name struck off the roll only in the next draft that finds it gone.
    """
    names = f"{context.fyrd_names} {'name' if context.fyrd_names == 1 else 'names'}"

    return CreatePlayerMonthLog(
        title=f"The village paid a geld of {context.silver} silver for {names} off the fyrd roll.",
        kind=PlayerMonthLog.KindChoices.KIND_GELD_CALLED,
        month=context.month,
        faction=context.faction,
    )
