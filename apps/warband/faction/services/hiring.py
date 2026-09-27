from apps.warband.faction.models.faction import Faction
from apps.warband.finance.models import Transaction

UNAFFORDABLE_REFUSAL = "You don't have enough silver to hire this mercenary."


def get_pub_hire_refusal(*, faction: Faction, hiring_price: int) -> str | None:
    """
    Why this faction may not hire a mercenary at "hiring_price" out of its pub, or None if it may.

    Handed the price rather than the man, because the caller has to read it once before anything
    moves him - see [Warrior.idle_surcharge] - and the figure refused here has to be the figure the
    player is then told he paid.

    The first of two enforcement points, and the one the player hears from.
    "handle_recruit_pub_mercenary" re-checks that the man is still on the shelf as a filtered delete,
    which is what keeps a double click from charging for him twice.
    """
    if Transaction.objects.current_balance(faction_id=faction.id) < hiring_price:
        return UNAFFORDABLE_REFUSAL

    return None
