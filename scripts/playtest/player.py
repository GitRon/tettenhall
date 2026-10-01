import random

from django.db import transaction
from queuebie.runner import handle_message

from apps.warband.faction.messages.commands.faction import OccupyFaction
from apps.warband.faction.messages.commands.warrior import DraftWarriorFromFyrd, RecruitPubMercenary
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.services.hiring import get_pub_hire_refusal
from apps.warband.finance.models import Transaction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.messages.commands.skirmish import AttackFaction, FinishRound, StartDuel
from apps.warband.skirmish.models.skirmish import Skirmish
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.skirmish.services.march import get_march_cost_refusal
from apps.warband.skirmish.services.skirmish.skirmish_participants import SkirmishParticipantBuilderService
from apps.warband.town.buildings import BUILDINGS
from apps.warband.town.buildings.hall import Hall
from apps.warband.town.buildings.marketplace import Marketplace
from apps.warband.town.buildings.sanctuary import Sanctuary
from apps.warband.town.buildings.weaponsmith import Weaponsmith
from apps.warband.town.messages.commands.town import UpgradeTownBuilding
from apps.warband.town.services.building_upgrade import get_building_upgrade_refusal
from apps.warband.warrior.messages.commands.warrior import RecruitCapturedWarrior
from apps.warband.warrior.services.availability import assess_roster
from scripts.playtest.policy import PlayerPolicy
from scripts.playtest.report import GameReport

# What the player never spends below, on a hire or a building, so the wage bill does not strand him
SILVER_KEPT_BACK = 150
# Each month the first of these that may be upgraded, and leaves the silver above, is built
BUILD_ORDER = (Hall.BUILDING_NAME, Sanctuary.BUILDING_NAME, Weaponsmith.BUILDING_NAME, Marketplace.BUILDING_NAME)
# A fight still undecided after this many rounds is one the harness cannot play out
MAX_ROUNDS = 300

STOP_FIGHT_STUCK = "fight could not be played out"


class PlayerTurn:
    """
    One month of the player's, dispatched the way the views dispatch it.

    Each step asks the refusal a view asks before it sends the command that view sends, in the order a
    player reaches them: the captives, the fyrd, the pub, the town, the march, the fight, the occupation.
    A guard that protects silver, men or the month is asked again by the command handler, so a step that
    skipped one would dispatch into a no-op rather than play a game nobody can play. The rule that lives
    only in a form - who may march - is taken from the same "assess_roster" the attack form validates
    against.

    The player's men fight the way the rival's do: each is given the action the game's own decision
    service picks for him. The harness adds no fighting judgement of its own.
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
    ) -> None:
        self.savegame = savegame
        self.faction = savegame.player_faction
        self.month = savegame.current_month
        self.policy = policy
        self.rng = rng
        self.report = report
        self.max_rounds = max_rounds

    def play(self) -> str | None:
        """Plays the month and says why the game cannot go on, if it cannot."""
        self.take_in_captives()
        self.draft_the_fyrd()
        self.hire_from_the_pub()
        self.build()
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

    def build(self) -> None:
        town = self.faction.town
        town.refresh_from_db()
        for building_type in BUILD_ORDER:
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

    def _healthy_men_of(self, *, faction: Faction) -> int:
        return Warrior.objects.filter_faction(faction_id=faction.id).filter_healthy().count()

    def march(self) -> str | None:
        """Marches on the rival with the fewest men on their feet, with everybody who may go."""
        targets = list(Faction.objects.attackable_by(savegame=self.savegame))
        leader = self.faction.get_available_leader(month=self.month)
        if not targets or leader is None:
            return None

        # The random draw breaks a tie between two equally weak rivals, from the policy's own generator
        target = min(targets, key=lambda rival: (self._healthy_men_of(faction=rival), self.rng.random()))
        roster = assess_roster(faction_id=self.faction.id, month=self.month, excluded_ids=(leader.id,))
        band = [leader, *Warrior.objects.filter(id__in=roster.available_ids).order_by("id")]

        if not self.policy.will_march(band_size=len(band), defenders=self._healthy_men_of(faction=target)):
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
                attacking_faction=self.faction, target_faction=target, assigned_warriors=band, month=self.month
            )
        )
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
