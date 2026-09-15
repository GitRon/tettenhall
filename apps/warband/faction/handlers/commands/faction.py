import random

from django.db.models import Q
from queuebie import message_registry
from queuebie.messages import Event

from apps.warband.faction.domain.occupation_spoils import OccupationSpoils
from apps.warband.faction.domain.rival_income import RivalIncome
from apps.warband.faction.messages.commands.faction import (
    ChangeFyrdReserve,
    CreateFactionsForNewSavegame,
    DefeatFactionOfLostLeader,
    EarnMoneyFromBuildings,
    EarnMonthlyFactionIncome,
    OccupyFaction,
    PrepareFactionWarriorsForMonth,
    ReplenishFyrdReserve,
    SetNewLeaderWarrior,
)
from apps.warband.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionWasDefeated,
    FactionWasOccupied,
    FyrdReserveChanged,
    MonthlyBuildingMoneyEarned,
    MonthlyFactionIncomeEarned,
    NewFactionCreated,
    NewLeaderWarriorSet,
)
from apps.warband.faction.messages.events.warrior import WarriorMonthPrepared
from apps.warband.faction.models import Culture
from apps.warband.faction.models.faction import Faction
from apps.warband.faction.services.faker import faker_for_locale
from apps.warband.finance.models import Transaction
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.skirmish.models.warrior import Warrior
from apps.warband.town.buildings.sanctuary import NPC_STARTING_SANCTUARY_LEVEL
from apps.warband.town.models import Town


def _create_faction(*, name: str, town_name: str, culture_id: int, savegame: Savegame, is_player: bool) -> Faction:
    """
    One faction and the one town it holds.

    A faction always has exactly one town, so it is part of creating one rather than a reaction to it:
    several handlers of NewFactionCreated already read faction.town, and an event handler emitting a
    CreateTown command would land in the same batch as those, with no guaranteed order.
    """
    faction = Faction.objects.create(
        name=name,
        town_name=town_name,
        culture_id=culture_id,
        savegame=savegame,
        fyrd_reserve=random.randint(2, 5),
    )

    if is_player:
        # Every building at its 0 default, "last_constructed_building_at" included, so the player can
        # build in month 1.
        Town.objects.create(faction=faction)
        savegame.player_faction = faction
        savegame.save()
    else:
        # A rival is handed the one building level that decides something for it. Nothing upgrades a
        # rival's town, so the sanctuary it is created with is the pace its wounded mend at for the
        # rest of the savegame, and it wants choosing rather than inheriting the level of a town that
        # has built nothing. The other three stay at 0: their levers price or stock something only
        # the player reaches.
        Town.objects.create(faction=faction, sanctuary=NPC_STARTING_SANCTUARY_LEVEL)

    return faction


@message_registry.register_command(command=CreateFactionsForNewSavegame)
def handle_create_factions_for_new_savegame(*, context: CreateFactionsForNewSavegame) -> list[Event]:
    """
    Turns a fresh savegame into a populated one: the player's faction plus a few rivals.

    This reads cultures from the database, which is why it is a command handler - the event handler
    emitting it runs under strict mode's database blocker.

    It does the creating itself rather than raising a command per faction. The one fact this topic has
    to announce is that a faction now exists, and nothing that only plans a creation can announce it -
    so the read and the write sit together and what leaves here is NewFactionCreated per faction.
    """
    player_culture = Culture.objects.get_or_none(id=context.faction_culture_id)
    # Cultures are reference data, so an id with no row behind it is a half-seeded database rather than
    # bad input, and it wants naming as such - the way the item generator does for its own fixture. This
    # guards the rival draw below as well: a culture coming back here is proof the table has rows for
    # "random.choice" to pick from.
    if player_culture is None:
        raise RuntimeError(
            f"Culture {context.faction_culture_id} does not exist. "
            f"Load the reference data with 'loaddata culture itemtype questname'."
        )

    # A rival dealt the player's own culture is named out of the same generator the player's war band
    # is, so the rivals list reads as one people under five flags - which is also the one thing the
    # player chose about his faction handed back to him as somebody else's.
    #
    # The player's culture is kept as the fallback rather than the draw failing: five cultures ship,
    # so this leaves four, but a database seeded with a single one would otherwise produce a savegame
    # with no rivals in it at all.
    rival_cultures = list(Culture.objects.exclude(id=player_culture.id)) or [player_culture]

    # The player's own faction first, because it is the one the savegame is pointed at and every
    # rival is drawn against a world he is already in
    faction_list = [
        _create_faction(
            name=context.faction_name,
            town_name=context.town_name,
            culture_id=context.faction_culture_id,
            savegame=context.savegame,
            is_player=True,
        )
    ]

    for _ in range(random.randint(3, 5)):
        rival_culture = random.choice(rival_cultures)
        # A rival is named in the culture on its own row, because that is the culture its warriors are
        # generated from - naming it from anything else puts a Norse town in front of a Frisian war band.
        faker = faker_for_locale(locale=rival_culture.locale)
        faction_list.append(
            _create_faction(
                name=faker.city(),
                town_name=faker.city(),
                culture_id=rival_culture.id,
                savegame=context.savegame,
                is_player=False,
            )
        )

    return [
        NewFactionCreated(faction=faction, current_month=context.savegame.current_month) for faction in faction_list
    ]


@message_registry.register_command(command=ReplenishFyrdReserve)
def handle_replenish_fyrd_reserve(*, context: ReplenishFyrdReserve) -> Event | None:
    new_recruits = random.randrange(0, 3)

    if new_recruits == 0:
        return None

    # Update faction
    Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruits=new_recruits)

    return FactionFyrdReserveReplenished(
        faction=context.faction,
        new_recruits=new_recruits,
        month=context.month,
    )


@message_registry.register_command(command=ChangeFyrdReserve)
def handle_change_fyrd_reserve(*, context: ChangeFyrdReserve) -> Event:
    """
    Move the reserve by the amount the caller named, in whichever direction that is.

    The manager floors a reduction at zero, so this cannot drive the column negative. A caller that
    cares what actually happened clamps its own request instead - the event repeats what was asked
    for, and a log line written from a number the reserve could not honour would be a lie.
    """
    if context.change >= 0:
        Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruits=context.change)
    else:
        Faction.objects.reduce_fyrd_reserve(faction=context.faction, drafted_warriors=-context.change)

    return FyrdReserveChanged(faction=context.faction, change=context.change, month=context.month)


@message_registry.register_command(command=PrepareFactionWarriorsForMonth)
def handle_prepare_faction_warriors_for_month(*, context: PrepareFactionWarriorsForMonth) -> list[Event]:
    """
    Every living man this faction is responsible for: its own roster, plus the captives it holds.

    A captive is on nobody's roster - capture clears "warrior.faction" - so without the second half
    he is reached by nothing for as long as he is held, and a prisoner taken unconscious stays at the
    health the blow that felled him left him at for ever. His captor's month reaches him exactly once:
    a warrior belongs to exactly one captor, and this runs once per faction per month.

    Matched by id rather than through the reverse accessor of "captured_warriors", which would join
    per captor row and hand the same man out twice were he ever held by two of them.

    Only the dead are filtered out, and that is the point rather than an oversight. The event this
    raises is a fact - this man entered a month - and it can only be one while the read is unfiltered;
    a sweep that selected the wounded would announce a state somebody looked up instead. What applies
    to a man is decided by the handlers subscribing, each with its own guard on the columns the event
    carries.

    "unpaid_months" is read here and travels on the event, so the morale reaction sees the counter the
    salary run wrote this same month. That write is synchronous inside the salary command handler and
    this command is declared after it, which is why the warriors are loaded here rather than earlier -
    and why there is a flow test on FinishMonthView pinning the outcome.
    """
    warrior_list = Warrior.objects.filter(
        Q(faction=context.faction) | Q(id__in=context.faction.captured_warriors.all())
    ).exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)

    return [
        WarriorMonthPrepared(faction=context.faction, warrior=warrior, month=context.month) for warrior in warrior_list
    ]


@message_registry.register_command(command=DefeatFactionOfLostLeader)
def handle_defeat_faction_of_lost_leader(*, context: DefeatFactionOfLostLeader) -> Event | None:
    """
    Knocks out the faction this warrior led, if he led one.

    Most warriors are nobody's leader, so the usual answer is None. "Faction.leader" is looked up
    rather than "warrior.faction" because capture clears the latter before this runs - the leader
    relation is the only remaining record of who led whom.

    The player's faction, the month and the fallen man are read here and put on the event, because
    the handlers announcing the knockout run under strict mode's database blocker and could not.
    """
    faction = (
        Faction.objects.still_in_play(savegame_id=context.warrior.savegame_id).filter(leader=context.warrior).first()
    )

    if faction is None:
        return None

    faction.is_defeated = True
    faction.save(update_fields=("is_defeated",))

    savegame = faction.savegame

    return FactionWasDefeated(
        faction=faction,
        savegame=savegame,
        player_faction=savegame.player_faction,
        leader=context.warrior,
        # Dead or merely taken, which is the difference between the two sentences the log can write.
        # A captured leader is knocked out first and taken afterwards, so anything but dead is taken
        leader_was_killed=context.warrior.is_dead,
        month=savegame.current_month,
    )


@message_registry.register_command(command=OccupyFaction)
def handle_occupy_faction(*, context: OccupyFaction) -> Event:
    """
    Rides into a town nobody healthy is left to hold.

    Does no work of its own: what an occupation costs the loser is the treasury and the leader, and
    both of those are somebody else's handler. This is where the two get looked up, because the event
    handlers taking them run under strict mode's database blocker and could not.

    The leader is read off the faction rather than off its roster - an unconscious leader is still the
    leader, and by the time this runs he is the only man the town has left. That he exists at all is
    "occupiable_by"'s doing, which is also the queryset the view resolved the target through.
    """
    plundered_silver = OccupationSpoils.get_plundered_silver(
        treasury=Transaction.objects.current_balance(faction_id=context.faction.id)
    )

    return FactionWasOccupied(
        faction=context.faction,
        occupying_faction=context.occupying_faction,
        leader=context.faction.leader,
        plundered_silver=plundered_silver,
        month=context.month,
    )


@message_registry.register_command(command=SetNewLeaderWarrior)
def handle_set_new_leader_warrior(*, context: SetNewLeaderWarrior) -> list[Event] | Event:
    context.faction.leader = context.warrior
    context.faction.save()

    return NewLeaderWarriorSet(faction=context.faction, warrior=context.warrior)


@message_registry.register_command(command=EarnMoneyFromBuildings)
def handle_earn_money_from_buildings(*, context: EarnMoneyFromBuildings) -> list[Event] | Event:
    """
    The town's monthly payout, for the one faction that builds.

    Never asked of a rival rather than refused for one: this hangs off PlayerMonthPrepared, the event
    for the things a rival has no equivalent of. A rival's town is created at every default and would
    collect NoHall's 50 silver against a leader's salary of around 135, whatever it fields - so
    letting rivals build their way out of that would be handing them a second income. They earn off
    their war band instead, see [RivalIncome].

    The men are counted here rather than inside the town, because the cost card asks the same
    question of the same faction a page earlier and the two have to get the same answer. Counted
    every month rather than stored: a player who hires in month twelve is paid the fuller revenue in
    month twelve, and one whose war band walks out is back to the baseline the month after.
    """
    warriors_on_payroll = Warrior.objects.filter_drawing_a_wage().filter_faction(faction_id=context.faction.id).count()

    return MonthlyBuildingMoneyEarned(
        faction=context.faction,
        amount=context.faction.town.get_monthly_income(warriors_on_payroll=warriors_on_payroll),
        month=context.month,
    )


@message_registry.register_command(command=EarnMonthlyFactionIncome)
def handle_earn_monthly_faction_income(*, context: EarnMonthlyFactionIncome) -> list[Event] | Event | None:
    """
    What a rival lives on, which is its war band rather than its town.

    Refused for the player, unlike the town income above: this one hangs off FactionMonthPrepared,
    which is raised for every faction and knows nothing about who they are, so the guard belongs here
    where reading the savegame is allowed. He has the buildings, and taking both would pay him twice
    for the same month.

    Counted over the healthy alone, while the wage bill covers everybody who is not dead - a faction
    that cannot field a warrior should not be earning off him. See [RivalIncome] for why the two
    rosters differ on purpose.
    """
    if context.faction.savegame.player_faction_id == context.faction.id:
        return None

    healthy_warriors = Warrior.objects.filter_healthy().filter_faction(faction_id=context.faction.id).count()

    return MonthlyFactionIncomeEarned(
        faction=context.faction,
        amount=RivalIncome.get_monthly_income(healthy_warriors=healthy_warriors),
        month=context.month,
    )
