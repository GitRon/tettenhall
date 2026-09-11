import random

from apps.warband.faction.models.culture import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.item.models.item_type import ItemType
from apps.warband.item.services.generators.item.base import BaseItemGenerator
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.warrior.domain.attribute_draw import AttributeDraw
from apps.warband.warrior.services.nickname import NICKNAME_VARIANT_BOUND, draw_nickname_state
from apps.warband.warrior.services.unique_name import draw_warrior_name


class BaseWarriorGenerator:
    XP_MU: int
    XP_SIGMA: int
    HEALTH_MU: int
    HEALTH_SIGMA: int
    MORALE_MU: int
    MORALE_SIGMA: int
    STATS_MU: int
    STATS_SIGMA: int
    STATS_MIN: int
    PROGRESS_MU: int
    PROGRESS_SIGMA: int

    # What a price is measured against, and the one pair of numbers on this class every archetype
    # shares rather than declaring its own. A price answers how good a man is, not how good he is
    # for his own kind: dividing a levy's rolled strength by a levy's mean and a mercenary's by a
    # mercenary's lands both near one, and the archetype cancels out of the very number it ought to
    # decide.
    #
    # The pair is the mercenary's own means, so a professional fighting man is what a full wage buys
    # and the other two archetypes fall out of their attributes instead of being asserted beside
    # them - a levy at roughly half of him because he has half the strength and two thirds of the
    # health, a leader at four fifths because he is steadier rather than stronger.
    #
    # Deliberately not "strength_baseline", which a fight scales a blow by (see
    # "Warrior.expected_damage"). That one is relative on purpose: a man of his own kind's average
    # deals his weapon's full damage. Relative is the right answer to what a blow is worth and the
    # wrong answer to what a man is worth, which is why pricing carries its own pair.
    PRICE_STATS_YARDSTICK = 10
    PRICE_HEALTH_YARDSTICK = 20

    item_generator_class: type(BaseItemGenerator)
    chance_for_weapon = 1
    chance_for_armor = 1

    # Whether this archetype is on the payroll at all. A wage is what a faction pays to keep a man it
    # decided to take on and could decide to let go, and the leader is neither: he is bought by
    # nobody, refused a dismissal by "get_dismissal_refusals", and exempt from the walk-out because
    # losing him defeats the faction. Billing for him would be billing for the one man the player
    # never chose and can never be rid of.
    #
    # It zeroes the wage and nothing else. "recruitment_price" stays as rolled, so
    # "slavery_selling_price" still says what a captured leader fetches - the one of the three
    # derived prices a leader can actually reach. The other two read off the wage and so read zero,
    # which is right for a man who is never hired and never sent away.
    draws_a_wage = True

    culture: Culture
    faction: Faction
    savegame_id: int

    def __init__(self, *, culture: Culture, faction: Faction | None, savegame_id: int) -> None:
        self.culture = culture
        self.faction = faction
        self.savegame_id = savegame_id

    def process(self) -> Warrior:
        # Every roll is rounded to the integer its column holds, and rounded before the guard sees
        # it. The guards compare against zero, and a raw "random.gauss" float of 0.42 satisfies them
        # and is then truncated to zero on the way into the column - a warrior with no health at
        # all, who cannot be wounded because his death threshold is zero, cannot be healed because
        # the monthly sweep asks for current below maximum, and draws a full wage regardless.
        # Rounding is what makes the guards real retries, and it keeps the instance handed back in
        # step with the row written, since Django does not re-read after a create.
        experience = 0
        while experience == 0:
            experience = max(round(random.gauss(self.XP_MU, self.XP_SIGMA)), 0)

        max_health = 0
        while max_health == 0:
            max_health = max(round(random.gauss(self.HEALTH_MU, self.HEALTH_SIGMA)), 0)

        health_progress = -1
        while health_progress < 0 or health_progress > 100:
            health_progress = max(round(random.gauss(self.PROGRESS_MU, self.PROGRESS_SIGMA)), 0)

        max_morale = 0
        while max_morale == 0:
            max_morale = max(round(random.gauss(self.MORALE_MU, self.MORALE_SIGMA)), 0)

        morale_progress = -1
        while morale_progress < 0 or morale_progress > 100:
            morale_progress = max(round(random.gauss(self.PROGRESS_MU, self.PROGRESS_SIGMA)), 0)

        # Floored at STATS_MIN rather than guarded and re-rolled: every generator sets a minimum of
        # at least one, so a stat cannot come out at zero the way health and morale can.
        strength = max(round(random.gauss(self.STATS_MU, self.STATS_SIGMA)), self.STATS_MIN)

        strength_progress = -1
        while strength_progress < 0 or strength_progress > 100:
            strength_progress = max(round(random.gauss(self.PROGRESS_MU, self.PROGRESS_SIGMA)), 0)

        dexterity = max(round(random.gauss(self.STATS_MU, self.STATS_SIGMA)), self.STATS_MIN)

        dexterity_progress = -1
        while dexterity_progress < 0 or dexterity_progress > 100:
            dexterity_progress = max(round(random.gauss(self.PROGRESS_MU, self.PROGRESS_SIGMA)), 0)

        base_recruitment_price = 0
        while base_recruitment_price == 0:
            base_recruitment_price = max(round(random.gauss(100, 50)), 0)
        recruitment_price = int(
            (((strength + dexterity) / self.PRICE_STATS_YARDSTICK) + (max_health / self.PRICE_HEALTH_YARDSTICK))
            * base_recruitment_price
        )

        # What he is remembered for, settled here and never again. The draws are built from the rolls
        # above rather than from a saved row, because the row does not exist yet - and the pairing is
        # the one the columns below stamp on him: both arms against the stats trio, health and morale
        # each against their own mean and spread.
        nickname_state = draw_nickname_state(
            strength=AttributeDraw(
                value=strength, baseline=self.STATS_MU, spread=self.STATS_SIGMA, minimum=self.STATS_MIN
            ),
            dexterity=AttributeDraw(
                value=dexterity, baseline=self.STATS_MU, spread=self.STATS_SIGMA, minimum=self.STATS_MIN
            ),
            health=AttributeDraw(value=max_health, baseline=self.HEALTH_MU, spread=self.HEALTH_SIGMA),
            morale=AttributeDraw(value=max_morale, baseline=self.MORALE_MU, spread=self.MORALE_SIGMA),
        )

        if random.uniform(0, 1) <= self.chance_for_weapon:
            weapon_generator = self.item_generator_class(
                faction=self.faction,
                item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
                savegame_id=self.savegame_id,
            )
            weapon = weapon_generator.process()
        else:
            weapon = None

        if random.uniform(0, 1) <= self.chance_for_armor:
            armor_generator = self.item_generator_class(
                faction=self.faction,
                item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
                savegame_id=self.savegame_id,
            )
            armor = armor_generator.process()
        else:
            armor = None

        return Warrior.objects.create(
            name=draw_warrior_name(culture=self.culture, savegame_id=self.savegame_id),
            culture=self.culture,
            faction=self.faction,
            savegame_id=self.savegame_id,
            experience=experience,
            current_health=max_health,
            max_health=max_health,
            health_progress=health_progress,
            # The health and morale distributions travel per attribute: their means and spreads stand
            # in no fixed ratio to the stats ones, so neither can be read off the other
            health_baseline=self.HEALTH_MU,
            health_spread=self.HEALTH_SIGMA,
            current_morale=max_morale,
            max_morale=max_morale,
            morale_progress=morale_progress,
            morale_baseline=self.MORALE_MU,
            morale_spread=self.MORALE_SIGMA,
            strength=strength,
            strength_progress=strength_progress,
            # What this warrior's strength is measured against in a fight: the mean of the archetype he
            # was drawn from, so a man of his own kind's average deals his weapon's full damage
            strength_baseline=self.STATS_MU,
            # And the spread of that population and the floor it rolls against, which together make
            # an extreme roll recognisable as one - see "get_nickname". Both cover dexterity too,
            # drawn as it is from the same sigma and the same minimum.
            stats_spread=self.STATS_SIGMA,
            stats_minimum=self.STATS_MIN,
            # Both drawn once and kept, so whatever he ends up being called he is called it
            # everywhere and for the rest of the savegame
            nickname_state=nickname_state,
            nickname_variant=random.randrange(NICKNAME_VARIANT_BOUND),
            dexterity=dexterity,
            dexterity_progress=dexterity_progress,
            recruitment_price=recruitment_price,
            # The share is the warrior's own number rather than this generator's, because the pub
            # prices a hire by inverting it - see "Warrior.hiring_price"
            monthly_salary=round(recruitment_price * Warrior.SALARY_SHARE_OF_PRICE) if self.draws_a_wage else 0,
            weapon=weapon,
            armor=armor,
        )
