from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.town.messages.events.town import FeastThrown
from apps.warband.warrior.messages.commands.warrior import ChangeWarriorMaxMorale


@message_registry.register_event(event=FeastThrown)
def handle_feast_mends_cut_ceilings(*, context: FeastThrown) -> list[Command]:
    """
    Every man at the table who carries a cut gets some of his nerve back.

    Through the same lever an incident pulls, asked for a repair rather than growth, so there is one
    path that moves a morale ceiling and not two. Who is mended is read off the columns the list
    already carries - strict mode forbids an event handler the database - and asking about a man with
    nothing to mend would only raise a zero further down.
    """
    return [
        ChangeWarriorMaxMorale(
            warrior=warrior,
            faction=context.faction,
            share=context.restored_share,
            month=context.month,
            restores_toward_peak=True,
        )
        for warrior in context.warrior_list
        if warrior.is_mended_by_a_feast
    ]
