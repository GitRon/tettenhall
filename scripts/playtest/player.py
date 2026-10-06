import random

from django.db import transaction
from queuebie.runner import handle_message

from apps.warband.faction.domain.rival_policy import RivalMonthSnapshot, RivalPolicy
from apps.warband.faction.messages.commands.faction import OccupyFaction
from apps.warband.faction.messages.commands.warrior import DraftWarriorFromFyrd, RecruitPubMercenary
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.services.hiring import get_pub_hire_refusal
from apps.warband.faction.services.purchase_snapshot import get_held_gear_values, get_shop_offers
from apps.warband.finance.models import Transaction
from apps.warband.item.messages.commands.item import BuyItem, EquipItem
from apps.warband.item.services.handout import plan_gear_handout
from apps.warband.quest.messages.commands.quest import AcceptQuest
from apps.warband.quest.models.quest import Quest
from apps.warband.quest.quests import QUESTS_BY_NAME
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.choices.raid_kind import RaidKindChoices
from apps.warband.skirmish.messages.commands.skirmish import AttackFaction, FinishRound, StartDuel
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.raids import RAID_KINDS
from apps.warband.skirmish.raids.kinds import LiftTheHerds, StormTheBurh
from apps.warband.skirmish.services.march import get_march_cost_refusal
from apps.warband.skirmish.services.skirmish.skirmish_participants import SkirmishParticipantBuilderService
from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.buildings.marketplace import Marketplace
from apps.warband.town.buildings.sanctuary import Sanctuary
from apps.warband.town.buildings.weaponsmith import Weaponsmith
from apps.warband.town.messages.commands.town import CallGeld, UpgradeTownBuilding
from apps.warband.town.services.building_upgrade import get_building_upgrade_refusal
from apps.warband.town.services.geld import GELD_FYRD_NAMES, GELD_SILVER, get_geld_refusal
from apps.warband.warrior.messages.commands.warrior import RecruitCapturedWarrior, TendWarriorWounds
from apps.warband.warrior.services.availability import assess_roster
from apps.warband.warrior.services.tending import get_tending_price, get_tending_refusal
from scripts.playtest.policy import PlayerPolicy
from scripts.playtest.report import GameReport

# What the player never spends below, on a hire or a building, so the wage bill does not strand him
SILVER_KEPT_BACK = 150
# Each month the first of these that may be upgraded, and leaves the silver above, is built
BUILD_ORDER = (Hall.BUILDING_NAME, Sanctuary.BUILDING_NAME, Weaponsmith.BUILDING_NAME, Marketplace.BUILDING_NAME)
# The same with the sanctuary first, for a player who tends his wounded: without it there is nothing to pay
TENDING_BUILD_ORDER = (
    Sanctuary.BUILDING_NAME,
    Hall.BUILDING_NAME,
    Weaponsmith.BUILDING_NAME,
    Marketplace.BUILDING_NAME,
)
# A fight still undecided after this many rounds is one the harness cannot play out
MAX_ROUNDS = 300

STOP_FIGHT_STUCK = "fight could not be played out"


class PlayerTurn:
    """
    One month of the player's, dispatched the way the views dispatch it.

    Each step asks the refusal a view asks before it sends the command that view sends, in the order a
    player reaches them: the captives, the fyrd, the pub, the shop, the stores, the town, the board, the
    march, the fight, the occupation.
    A guard that protects silver, men or the month is asked again by the command handler, so a step that
    skipped one would dispatch into a no-op rather than play a game nobody can play. The rule that lives
    only in a form - who may march - is taken from the same "assess_roster" the attack form validates
    against.

    The player's men fight the way the rival's do: each is given the action the game's own decision
    service picks for him. The harness adds no fighting judgement of its own.

    "tending" plays a player who pays his sanctuary to mend his wounded: the sanctuary comes first in the
    build order, and the wounded are tended straight after the fyrd, before the pub and the shop have
    spent the purse down. Off by default, so a batch measures what it always measured; a question about
    the price of tending switches it on for both of the batches it compares.

    "geld" plays a player who taxes his village when the purse runs low: before the fyrd is drafted, while
    there is still a name on the roll to strike, a geld is called whenever the purse is below the silver
    kept back. Off by default for the reason tending is.
    """

    savegame: Savegame
    faction: Faction
    month: int

    def __init__(
        self,
        *,
        savegame: Savegame,
        policy: PlayerPolicy,
        rng: random.Random,
        report: GameReport,
        max_rounds: int = MAX_ROUNDS,
        tending: bool = False,
        geld: bool = False,
    ) -> None:
        self.savegame = savegame
        self.faction = savegame.player_faction
        self.month = savegame.current_month
        self.policy = policy
        self.rng = rng
        self.report = report
        self.max_rounds = max_rounds
        self.tending = tending
        self.geld = geld
        # Who was on the roster as the band set out - the steps before the march add men to it, so a
        # successor raised by the fight is told apart against this rather than against last month's roster
        self.roster_ids_at_march: frozenset[int] = frozenset()

    def play(self) -> str | None:
        """Plays the month and says why the game cannot go on, if it cannot."""
        self.take_in_captives()
        if self.geld:
            self.call_a_geld()
        self.draft_the_fyrd()
        if self.tending:
            self.tend_the_wounded()
        self.hire_from_the_pub()
        self.buy_from_the_shop()
        self.hand_out_gear()
        self.build()
        self.send_men_on_the_steady_work()
        self.roster_ids_at_march = frozenset(
            Warrior.objects.filter_faction(faction_id=self.faction.id).values_list("id", flat=True)
        )
        stop_reason = self.march()
        if stop_reason is not None:
            return stop_reason

        # After the march rather than inside it: a town left with nobody to hold it can be ridden into
        # whether or not this month's fight is what emptied it
        self.occupy()
        return None

    def _balance(self) -> int:
        return Transaction.objects.current_balance(faction_id=self.faction.id)

    def take_in_captives(self) -> None:
        for warrior in self.faction.captured_warriors.all():
            handle_message(RecruitCapturedWarrior(faction=self.faction, warrior=warrior, month=self.month))
            self.report.captives_recruited += 1

    def call_a_geld(self) -> None:
        """
        Only while the purse is below what the player keeps back: a geld costs a man the draft would
        have raised for free, so a player with silver to spare has no reason to sell one.
        """
        if self._balance() >= SILVER_KEPT_BACK:
            return

        self.faction.refresh_from_db()
        if get_geld_refusal(town=self.faction.town, faction=self.faction, current_savegame=self.savegame) is not None:
            return

        handle_message(
            CallGeld(
                town=self.faction.town,
                faction=self.faction,
                silver=GELD_SILVER,
                fyrd_names=GELD_FYRD_NAMES,
                month=self.month,
            )
        )
        self.report.gelds_called += 1

    def draft_the_fyrd(self) -> None:
        self.faction.refresh_from_db()
        for _free_man in range(self.faction.fyrd_reserve):
            handle_message(DraftWarriorFromFyrd(faction=self.faction, month=self.month))
            self.report.drafted += 1

    def hire_from_the_pub(self) -> None:
        # Cheapest first, and the first one he cannot afford ends the round: everybody after him costs more
        for mercenary in sorted(Warrior.objects.in_pub_of(faction_id=self.faction.id), key=lambda m: m.hiring_price):
            # Read once and before the message, as the view does: hiring him clears what his price is made of
            hiring_price = mercenary.hiring_price
            if self._balance() - hiring_price < SILVER_KEPT_BACK or get_pub_hire_refusal(
                faction=self.faction, hiring_price=hiring_price
            ):
                return
            handle_message(RecruitPubMercenary(warrior=mercenary, faction=self.faction, month=self.month))
            self.report.hired += 1

    def buy_from_the_shop(self) -> None:
        """
        Buys off the shelf by the rule a rival buys by, so the two sides of a batch shop alike.

        [RivalPolicy] is handed the shelf and the band's gear and nothing else - no fyrd, no pub and no hall,
        so only an item is ever a candidate: the steps before have taken the rest. The purse
        it weighs is what lies above SILVER_KEPT_BACK, against no wage bill, so a purchase is affordable
        exactly when it leaves the silver this harness keeps back for every other spend.

        The view's "get_purchase_refusal" is not asked: it refuses a price above the purse, and the
        policy keeps a running purse that never lets one through. "handle_buy_item" re-reads the purse
        all the same.
        """
        item_by_id = {item.id: item for item in self.faction.available_items.select_related("type")}
        snapshot = RivalMonthSnapshot(
            fyrd_reserve=0,
            purse=self._balance() - SILVER_KEPT_BACK,
            wage_bill=0,
            warriors_on_payroll=0,
            draft_wage=0,
            pub_offer_list=[],
            shop_offer_list=get_shop_offers(item_list=item_by_id.values()),
            held_gear_values=get_held_gear_values(faction=self.faction),
        )

        # Every decision is a purchase, since a man was never a candidate
        for decision in RivalPolicy.decide(snapshot=snapshot):
            item = item_by_id[decision.item_id]
            handle_message(BuyItem(price=item.price, item=item, buying_faction=self.faction, month=self.month))
            self.report.items_bought += 1

    def hand_out_gear(self) -> None:
        """
        Puts the best of what the faction holds on its best men, the way a rival's hand-out does - the
        purchases just made and any spoils lying in the stores alike.

        The view's "get_equip_refusal" is not asked: it refuses a man standing in an open fight, at either
        end of the move, and "plan_gear_handout" leaves those men and what they hold out of its plan.
        """
        for warrior, item, slot in plan_gear_handout(faction=self.faction):
            handle_message(EquipItem(warrior=warrior, item=item, slot=slot))
            self.report.items_equipped += 1

    def build(self) -> None:
        town = self.faction.town
        town.refresh_from_db()
        for building_type in TENDING_BUILD_ORDER if self.tending else BUILD_ORDER:
            if get_building_upgrade_refusal(town=town, building_type=building_type, current_savegame=self.savegame):
                continue
            new_level = getattr(town, building_type) + 1
            costs = BUILDINGS[building_type].get_building_by_type(building_type=new_level).BUILDING_COSTS
            if self._balance() - costs < SILVER_KEPT_BACK:
                continue
            handle_message(
                UpgradeTownBuilding(
                    town=town,
                    faction=self.faction,
                    building_type=building_type,
                    new_level=new_level,
                    costs=costs,
                    month=self.month,
                )
            )
            self.report.built.append((self.month, building_type, new_level))
            return

    def send_men_on_the_steady_work(self) -> None:
        """
        Sends the fewest men the month's steady work takes, the weakest at its attribute first.

        The leader stays home, so the band can still march: the harness spends men on the board only
        where it costs the march least. The men are those the accept form would offer.
        """
        leader_id = self.faction.leader_id
        for quest in Quest.objects.for_player_faction(faction_id=self.faction.id).offered_in(month=self.month):
            entry = QUESTS_BY_NAME[quest.quest]
            if not entry.IS_STEADY_WORK:
                continue

            roster = assess_roster(faction_id=self.faction.id, month=self.month, excluded_ids=(leader_id,))
            candidates = sorted(
                Warrior.objects.filter(id__in=roster.available_ids),
                key=lambda warrior: (getattr(warrior, entry.LEANS_ON), warrior.id),
            )
            if len(candidates) < entry.MIN_MEN:
                return

            band = candidates[: entry.MIN_MEN]
            handle_message(
                AcceptQuest(accepting_faction=self.faction, quest=quest, assigned_warriors=band, month=self.month)
            )
            self.report.sent_on_quests += len(band)
            return

    def tend_the_wounded(self) -> None:
        """
        Pays the sanctuary to mend the men who could march this month, the worst wounded first.

        Only the men who are free to march - nobody has been sent on the steady work yet, and nobody who stands
        in a fight already this month could fight again. Each is asked the refusal the tend view asks,
        against the purse above SILVER_KEPT_BACK, so a man too dear to mend is passed over and a less
        hurt one behind him may still be.
        """
        roster = assess_roster(faction_id=self.faction.id, month=self.month)
        wounded = sorted(
            Warrior.objects.filter(id__in=roster.available_ids),
            key=lambda warrior: (warrior.current_health - warrior.max_health, warrior.id),
        )
        for warrior in wounded:
            if get_tending_refusal(
                warrior=warrior, faction=self.faction, month=self.month, balance=self._balance() - SILVER_KEPT_BACK
            ):
                continue
            costs = get_tending_price(warrior=warrior, town=self.faction.town)
            handle_message(TendWarriorWounds(warrior=warrior, faction=self.faction, costs=costs, month=self.month))
            self.report.warriors_tended += 1

    def _healthy_men_of(self, *, faction: Faction) -> int:
        return Warrior.objects.filter_faction(faction_id=faction.id).filter_healthy().count()

    def march(self) -> str | None:
        """
        Marches on the rival with the fewest men on their feet, with everybody who may go.

        It storms the burh when the policy's margin allows over the rival's men and the burh's fyrd, and
        otherwise lifts the herds or stays home, as the policy says.
        """
        targets = list(Faction.objects.attackable_by(savegame=self.savegame))
        leader = self.faction.get_available_leader(month=self.month)
        if not targets or leader is None:
            return None

        # The random draw breaks a tie between two equally weak rivals, from the policy's own generator
        target = min(targets, key=lambda rival: (self._healthy_men_of(faction=rival), self.rng.random()))
        roster = assess_roster(faction_id=self.faction.id, month=self.month, excluded_ids=(leader.id,))
        band = [leader, *Warrior.objects.filter(id__in=roster.available_ids).order_by("id")]

        # Counted the way the attack page shows a raid to the player: the rival's men who would stand there,
        # and the people of the place who turn out beside them
        healthy_men = self._healthy_men_of(faction=target)
        if self.policy.will_march(band_size=len(band), defenders=healthy_men + StormTheBurh.LOCALS_TURNOUT):
            raid_kind = RaidKindChoices.STORM_THE_BURH
        elif self.policy.raids_when_outnumbered and self.policy.will_march(
            band_size=len(band), defenders=healthy_men // len(RAID_KINDS) + LiftTheHerds.LOCALS_TURNOUT
        ):
            # Too few to storm the burh, so out to the pastures, where a share of them stands on average
            raid_kind = RaidKindChoices.LIFT_THE_HERDS
        else:
            self.report.marches_held_back += 1
            return None

        # The last men to join stay at home until the march is affordable. The leader always goes.
        while len(band) > 1 and get_march_cost_refusal(
            faction_id=self.faction.id, month=self.month, warrior_count=len(band)
        ):
            band.pop()
        if get_march_cost_refusal(faction_id=self.faction.id, month=self.month, warrior_count=len(band)):
            self.report.marches_unaffordable += 1
            return None

        handle_message(
            AttackFaction(
                attacking_faction=self.faction,
                target_faction=target,
                assigned_warriors=band,
                raid_kind=raid_kind,
                month=self.month,
            )
        )
        if raid_kind == RaidKindChoices.LIFT_THE_HERDS:
            self.report.herd_raids += 1
        # Read back the way "FactionAttackView.get_success_url" reads it: a war band marches once a month
        skirmish = Skirmish.objects.filter(
            attacking_faction=self.faction, defending_faction=target, month=self.month
        ).latest("id")

        return self.fight(skirmish=skirmish)

    def fight(self, *, skirmish: Skirmish) -> str | None:
        """Plays rounds until the fight has a victor, as the Fight! button would."""
        for _round in range(self.max_rounds):
            skirmish = Skirmish.objects.prefetch_related("attacking_warriors", "defending_warriors").get(pk=skirmish.pk)
            if skirmish.victorious_faction_id:
                if skirmish.victorious_faction_id == self.faction.id:
                    self.report.fights_won += 1
                else:
                    self.report.fights_lost += 1
                return None

            own_side = (
                skirmish.attacking_warriors.all()
                if skirmish.attacking_faction_id == self.faction.id
                else skirmish.defending_warriors.all()
            )
            posted = [
                (warrior.id, warrior.decide_skirmish_action(skirmish=skirmish)[0])
                for warrior in own_side
                if warrior.is_healthy
            ]
            attacking, defending = SkirmishParticipantBuilderService(
                skirmish=skirmish, participants=posted, player_faction_id=self.faction.id
            ).process()
            # The view answers this with a 400: a side with nobody on it is not a fight
            if not attacking or not defending:
                return STOP_FIGHT_STUCK

            # One transaction around both, for the reason "SkirmishFinishRoundView.post" gives
            with transaction.atomic():
                handle_message(
                    StartDuel(skirmish=skirmish, skirmish_participants_1=attacking, skirmish_participants_2=defending)
                )
                handle_message(FinishRound(skirmish=skirmish, month=self.month))

        return STOP_FIGHT_STUCK

    def occupy(self) -> None:
        savegame = Savegame.objects.select_related("player_faction").get(pk=self.savegame.pk)
        for rival in Faction.objects.occupiable_by(savegame=savegame):
            handle_message(OccupyFaction(faction=rival, occupying_faction=self.faction, month=self.month))
            self.report.occupations += 1
