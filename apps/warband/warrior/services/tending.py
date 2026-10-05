from apps.warband.faction.models.faction import Faction
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.buildings.sanctuary import Sanctuary
from apps.warband.town.models import Town

DEAD_REFUSAL = "He is past tending."
NOT_YOUR_MAN_REFUSAL = "Only the men under your banner are tended at your sanctuary."
UNWOUNDED_REFUSAL = "He has no wounds to tend."
NO_SANCTUARY_REFUSAL = "There is no sanctuary to tend him in. Build one first."
OPEN_FIGHT_REFUSAL = "He stands in a fight that has not been played out yet."
ALREADY_TENDED_THIS_MONTH_REFUSAL = "His wounds have already been tended this month."
UNAFFORDABLE_REFUSAL = "You don't have the silver to have him tended."


def get_tending_price(*, warrior: Warrior, town: Town) -> int:
    """
    What "town"'s sanctuary charges to mend this man to full health, per point he is missing.
    """
    sanctuary = Sanctuary.get_building_by_type(building_type=town.sanctuary)

    return sanctuary.get_tending_price(missing_health=warrior.max_health - warrior.current_health)


def get_tending_refusal(*, warrior: Warrior, faction: Faction, month: int, balance: int) -> str | None:
    """
    Why "faction" may not pay its sanctuary to tend this man now, or None if it may.

    First refusal wins, in the order "get_feast_refusal" reports its own: what the player can do
    least about is named first. Nothing will bring back a dead man or make another faction's man his,
    a man at full health has nothing to buy, a sanctuary is built rather than waited for, a fight ends
    once it is played out and the month once it is over - and the price is the one thing he can go
    and raise silver for.

    The page offering the control and the view dispatching the command both ask this, so the two
    cannot disagree about one man. "handle_tend_warrior_wounds" re-checks every rule but the building
    as one conditional UPDATE, so a double-click is charged once.
    """
    if warrior.condition == Warrior.ConditionChoices.CONDITION_DEAD:
        return DEAD_REFUSAL

    # A captive has no faction at all, so this is the cells and a rival's roster in one question:
    # the man in the cells keeps mending from his captor's sanctuary month by month, as before
    if warrior.faction_id != faction.id:
        return NOT_YOUR_MAN_REFUSAL

    if warrior.current_health >= warrior.max_health:
        return UNWOUNDED_REFUSAL

    sanctuary = Sanctuary.get_building_by_type(building_type=faction.town.sanctuary)
    if not sanctuary.can_tend():
        return NO_SANCTUARY_REFUSAL

    # A fight nobody has played out reads his health as it goes - the same question that keeps his
    # gear locked to him
    if Warrior.objects.filter_standing_in_an_open_fight().filter(id=warrior.id).exists():
        return OPEN_FIGHT_REFUSAL

    if warrior.last_tended_at == month:
        return ALREADY_TENDED_THIS_MONTH_REFUSAL

    if balance < get_tending_price(warrior=warrior, town=faction.town):
        return UNAFFORDABLE_REFUSAL

    return None


def was_tended(*, warrior: Warrior, month: int) -> bool:
    """
    Whether this man's wounds were tended for silver in "month", read off the row.

    What the tend view asks after it dispatches, so a request that lost its purse to another spend is
    not told he was mended.
    """
    return Warrior.objects.filter(id=warrior.id, last_tended_at=month).exists()
