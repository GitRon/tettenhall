import random

from apps.warband.faction.models.faction import Faction
from apps.warband.quest.quests import ERRANDS_OFFERED, QUESTS, STEADY_WORK_OFFERED
from apps.warband.quest.quests.base import Quest


def draw_quests_to_offer(*, faction: Faction) -> list[type[Quest]]:
    """
    The entries a month offers this faction: its steady work first, then the rest of the catalogue.

    Two draws rather than one pool, so steady work is on the board every month whatever else is - the
    one errand a war band that cannot pay its men can always send them on. Within each side an entry
    is drawn at most once, weighted against the others still in it.
    """
    possible = [quest for quest in QUESTS if quest.is_possible(faction=faction)]

    return [
        *_draw_without_repeats(
            candidates=[quest for quest in possible if quest.IS_STEADY_WORK], count=STEADY_WORK_OFFERED
        ),
        *_draw_without_repeats(
            candidates=[quest for quest in possible if not quest.IS_STEADY_WORK], count=ERRANDS_OFFERED
        ),
    ]


def _draw_without_repeats(*, candidates: list[type[Quest]], count: int) -> list[type[Quest]]:
    drawn = []
    remaining = list(candidates)

    while remaining and len(drawn) < count:
        quest = random.choices(remaining, weights=[candidate.WEIGHT for candidate in remaining])[0]
        drawn.append(quest)
        remaining.remove(quest)

    return drawn
