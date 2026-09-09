from queuebie import message_registry
from queuebie.messages import Command

from apps.warband.faction.messages.events.item import TownShopRestocked
from apps.warband.faction.messages.events.quest import BulletinBoardQuestsOffered
from apps.warband.faction.messages.events.warrior import TownMercenariesRestocked
from apps.warband.month.messages.commands.month import CreatePlayerMonthLog
from apps.warband.month.models.player_month_log import PlayerMonthLog


@message_registry.register_event(event=BulletinBoardQuestsOffered)
def handle_bulletin_board_quests_offered(*, context: BulletinBoardQuestsOffered) -> Command:
    return CreatePlayerMonthLog(
        title=f"The bulletin board is offering {context.new_quests} new quest{'' if context.new_quests == 1 else 's'}.",
        kind=PlayerMonthLog.KindChoices.KIND_QUESTS_OFFERED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=TownMercenariesRestocked)
def handle_town_mercenaries_restocked(*, context: TownMercenariesRestocked) -> Command:
    return CreatePlayerMonthLog(
        title=f"The pub has filled with {context.new_mercenaries} "
        f"mercenar{'y' if context.new_mercenaries == 1 else 'ies'} for hire.",
        kind=PlayerMonthLog.KindChoices.KIND_PUB_RESTOCKED,
        month=context.month,
        faction=context.faction,
    )


@message_registry.register_event(event=TownShopRestocked)
def handle_town_shop_restocked(*, context: TownShopRestocked) -> Command:
    return CreatePlayerMonthLog(
        title=f"The shop has taken {context.new_items} new item{'' if context.new_items == 1 else 's'} into stock.",
        kind=PlayerMonthLog.KindChoices.KIND_SHOP_RESTOCKED,
        month=context.month,
        faction=context.faction,
    )
