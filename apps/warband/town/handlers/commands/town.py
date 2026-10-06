from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.faction.models import Faction
from apps.warband.finance.models import Transaction
from apps.warband.town.messages.commands.town import CallGeld, ThrowFeast, UpgradeTownBuilding
from apps.warband.town.messages.events.town import FeastThrown, GeldCalled, TownBuildingUpgraded
from apps.warband.town.models import Town


@message_registry.register_command(command=UpgradeTownBuilding)
def handle_upgrade_town_building(*, context: UpgradeTownBuilding) -> Event | None:
    # Only while the purse still covers it: a building and a purchase elsewhere can each pass their
    # view's check on the same balance, and only the one that gets the write lock first may spend it.
    # A read rather than a conditional write, because no row holds the balance to write against.
    if Transaction.objects.current_balance(faction_id=context.faction.id) < context.costs:
        return None

    # One conditional UPDATE rather than read-modify-save, so the once-per-month rule survives two
    # overlapping requests. The view checks the same guard to give the player a message, but both
    # requests pass that check on a double-clicked button, and only one of them may be charged.
    upgraded_rows = (
        Town.objects.filter(pk=context.town.pk)
        .exclude(last_constructed_building_at=context.month)
        .update(**{context.building_type: context.new_level}, last_constructed_building_at=context.month)
    )
    if not upgraded_rows:
        return None

    # The UPDATE went around the instance, so bring it in line for the handlers downstream
    setattr(context.town, context.building_type, context.new_level)
    context.town.last_constructed_building_at = context.month

    return TownBuildingUpgraded(
        town=context.town,
        faction=context.faction,
        building_type=context.building_type,
        new_level=context.new_level,
        costs=context.costs,
        month=context.month,
    )


@message_registry.register_command(command=ThrowFeast)
def handle_throw_feast(*, context: ThrowFeast) -> Event | None:
    # The purse first, for the reason the building upgrade above gives
    if Transaction.objects.current_balance(faction_id=context.faction.id) < context.costs:
        return None

    # The once-a-month rule as one conditional UPDATE, for the reason the building upgrade above gives:
    # a double-clicked button passes the view's check twice, and only one of the two may be charged
    feasted_rows = (
        Town.objects.filter(pk=context.town.pk).exclude(last_feast_at=context.month).update(last_feast_at=context.month)
    )
    if not feasted_rows:
        return None

    context.town.last_feast_at = context.month

    return FeastThrown(
        town=context.town,
        faction=context.faction,
        warrior_list=context.warrior_list,
        restored_share=context.restored_share,
        costs=context.costs,
        month=context.month,
    )


@message_registry.register_command(command=CallGeld)
def handle_call_geld(*, context: CallGeld) -> Event | None:
    # The roll first, read rather than written, the way the purse is above: a draft in another tab may
    # have emptied it after the view asked, and this request's write lock is what keeps one from doing so
    # between this read and the strike. Without it the village would pay for a name it no longer has.
    if not Faction.objects.filter(pk=context.faction.pk, fyrd_reserve__gte=context.fyrd_names).exists():
        return None

    # The once-a-month rule as one conditional UPDATE, for the reason the building upgrade above gives:
    # a double-clicked button passes the view's check twice, and the village may only pay once
    gelded_rows = (
        Town.objects.filter(pk=context.town.pk).exclude(last_geld_at=context.month).update(last_geld_at=context.month)
    )
    if not gelded_rows:
        return None

    context.town.last_geld_at = context.month

    return GeldCalled(
        town=context.town,
        faction=context.faction,
        silver=context.silver,
        fyrd_names=context.fyrd_names,
        month=context.month,
    )
