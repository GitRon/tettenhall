import random

from django.db.models import F, Q
from faker import Faker
from queuebie import message_registry
from queuebie.messages import Command, Event

from apps.faction.messages.commands.faction import (
    CreateFactionsForNewSavegame,
    CreateNewFaction,
    DefeatFactionOfLostLeader,
    DetermineInjuredWarriors,
    DetermineWarriorsWithReducedMorale,
    EarnMoneyFromBuildings,
    RemoveQuestFromBulletinBoard,
    ReplenishFyrdReserve,
    RestockTownShopItems,
    SetNewLeaderWarrior,
)
from apps.faction.messages.events.faction import (
    FactionFyrdReserveReplenished,
    FactionWarriorsWithReducedMoraleDetermined,
    FactionWasDefeated,
    MonthlyBuildingMoneyEarned,
    NewFactionCreated,
    NewLeaderWarriorSet,
    QuestWasRemovedFromBulletinBoard,
    RequestNewItemForTownShop,
)
from apps.faction.models import Culture
from apps.faction.models.faction import Faction
from apps.item.models import ItemType
from apps.item.services.generators.item.mercenary import MercenaryItemGenerator
from apps.skirmish.models.warrior import Warrior
from apps.town.buildings.hall import Hall
from apps.town.buildings.marketplace import Marketplace
from apps.town.buildings.weaponsmith import Weaponsmith
from apps.town.models import Town
from apps.warrior.messages.commands.warrior import HealInjuredWarrior


@message_registry.register_command(command=CreateFactionsForNewSavegame)
def handle_create_factions_for_new_savegame(*, context: CreateFactionsForNewSavegame) -> list[Command]:
    """
    Turns a fresh savegame into a populated one: the player's faction plus a few rivals.

    This reads cultures from the database, which is why it is a command handler - the event handler
    emitting it runs under strict mode's database blocker.
    """
    culture = Culture.objects.get_or_none(id=context.faction_culture_id)
    # Cultures are reference data, and a database missing them used to die one line down on
    # "NoneType has no attribute locale". Says what is missing instead, the way the item generator
    # already does for its own fixture. This guards the rival draw below as well: a culture coming
    # back here is proof the table has rows for "random.choice" to pick from.
    if culture is None:
        raise RuntimeError(
            f"Culture {context.faction_culture_id} does not exist. "
            f"Load the reference data with 'loaddata culture itemtype'."
        )

    faker = Faker([culture.locale])

    return [
        CreateNewFaction(
            name=context.faction_name,
            town_name=context.town_name,
            savegame=context.savegame,
            culture_id=context.faction_culture_id,
            is_player_faction=True,
        )
    ] + [
        CreateNewFaction(
            name=faker.city(),
            town_name=faker.city(),
            culture_id=random.choice(Culture.objects.all()).id,
            savegame=context.savegame,
            is_player_faction=False,
        )
        for _ in range(random.randint(3, 5))
    ]


@message_registry.register_command(command=CreateNewFaction)
def handle_create_new_faction(*, context: CreateNewFaction) -> list[Event] | Event:
    faction = Faction.objects.create(
        name=context.name,
        town_name=context.town_name,
        culture_id=context.culture_id,
        savegame=context.savegame,
        fyrd_reserve=random.randint(2, 5),
    )

    # A faction always has exactly one town, so it is part of creating one rather than a reaction to
    # it: several handlers of NewFactionCreated already read faction.town, and an event handler
    # emitting a CreateTown command would land in the same batch as those, with no guaranteed order.
    # "last_constructed_building_at" stays at its 0 default so the player can build in month 1.
    Town.objects.create(faction=faction)

    # Set player faction in savegame
    if context.is_player_faction:
        context.savegame.player_faction = faction
        context.savegame.save()

    return NewFactionCreated(
        faction=faction,
        current_month=context.savegame.current_month,
    )


@message_registry.register_command(command=RestockTownShopItems)
def handle_restock_shop_items(*, context: RestockTownShopItems) -> list[Event] | Event:
    # TODO: in item.py?
    # Clean up previous stock
    context.faction.available_items.all().delete()

    message_list = []

    # The market decides how many stalls there are, the weaponsmith how good their wares
    marketplace = Marketplace.get_building_by_type(building_type=context.faction.town.marketplace)
    weaponsmith = Weaponsmith.get_building_by_type(building_type=context.faction.town.weaponsmith)

    for _ in range(marketplace.AVAILABLE_ITEMS):
        if bool(random.getrandbits(1)):
            message_list.append(
                RequestNewItemForTownShop(
                    faction=context.faction,
                    generator_class=MercenaryItemGenerator,
                    item_function=ItemType.FunctionChoices.FUNCTION_WEAPON,
                    month=context.month,
                    quality_bonus=weaponsmith.QUALITY_BONUS,
                )
            )
        else:
            message_list.append(
                RequestNewItemForTownShop(
                    faction=context.faction,
                    generator_class=MercenaryItemGenerator,
                    item_function=ItemType.FunctionChoices.FUNCTION_ARMOR,
                    month=context.month,
                    quality_bonus=weaponsmith.QUALITY_BONUS,
                )
            )

    return message_list


@message_registry.register_command(command=RemoveQuestFromBulletinBoard)
def handle_remove_quest_from_bulletin_board(*, context: RemoveQuestFromBulletinBoard) -> Event:
    # TODO: in quest.py?
    context.faction.available_quests.remove(context.quest)

    return QuestWasRemovedFromBulletinBoard(faction=context.faction, quest=context.quest, month=context.month)


@message_registry.register_command(command=ReplenishFyrdReserve)
def handle_replenish_fyrd_reserve(*, context: ReplenishFyrdReserve) -> Event | None:
    new_recruitees = random.randrange(0, 3)

    if new_recruitees == 0:
        return None

    # Update faction
    Faction.objects.replenish_fyrd_reserve(faction=context.faction, new_recruitees=new_recruitees)

    return FactionFyrdReserveReplenished(
        faction=context.faction,
        new_recruitees=new_recruitees,
        month=context.month,
    )


@message_registry.register_command(command=DetermineWarriorsWithReducedMorale)
def handle_determine_warriors_with_reduced_morale(*, context: DetermineWarriorsWithReducedMorale) -> Event:
    # The roster only, captives deliberately excluded - unlike the healing sweep below, which does
    # reach them. Health is what a captor can mend; spirit is not, and
    # "handle_replenish_warrior_morale" refills to the maximum unconditionally, so a month in an
    # enemy cell would restore a man completely.
    #
    # Settled, not an oversight left next to a healing sweep that was taught the opposite lesson: a
    # captive keeps whatever morale the fight left him for as long as he is held, and only starts
    # recovering once "handle_recruit_captured_warrior" puts him on a roster and this sweep reaches
    # him the following month. Nobody is stranded routed by it either - prisoners are taken from the
    # unconscious alone ("handle_finish_skirmish"), and a man who fled the field walked off it.
    #
    # Only warriors below their maximum have anything to recover - replenishing the rest would be
    # a no-op further down the chain
    warrior_qs = context.faction.warriors.exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD).filter(
        current_morale__lt=F("max_morale")
    )

    return FactionWarriorsWithReducedMoraleDetermined(
        faction=context.faction,
        warrior_list=list(warrior_qs),
        month=context.month,
    )


@message_registry.register_command(command=DetermineInjuredWarriors)
def handle_determine_injured_warriors(*, context: DetermineInjuredWarriors) -> list[Command]:
    """
    Every injured man this faction is responsible for: its own roster, plus the captives it holds.

    A captive is on nobody's roster - capture clears "warrior.faction" - so without the second half
    he heals nothing for as long as he is held, and a prisoner taken unconscious stays at the health
    the blow that felled him left him at for ever.

    Healing him from his captor's sweep reaches him exactly once: a warrior belongs to exactly one
    captor, and this runs once per faction per month. The captor rides along on the command because
    it is his sanctuary that does the mending and his month log the line belongs in - the healing
    handler cannot read either off a warrior whose own faction is None.

    Matched by id rather than through the reverse accessor of "captured_warriors", which would join
    per captor row and hand the same man out twice were he ever held by two of them.
    """
    warrior_qs = (
        Warrior.objects.filter(Q(faction=context.faction) | Q(id__in=context.faction.captured_warriors.all()))
        .exclude(condition=Warrior.ConditionChoices.CONDITION_DEAD)
        .filter(current_health__lt=F("max_health"))
    )

    event_list = []
    for warrior in warrior_qs:
        event_list.append(
            # TODO: this should be an event, not a command
            HealInjuredWarrior(
                faction=context.faction,
                warrior=warrior,
                month=context.month,
            )
        )

    return event_list


@message_registry.register_command(command=DefeatFactionOfLostLeader)
def handle_defeat_faction_of_lost_leader(*, context: DefeatFactionOfLostLeader) -> Event | None:
    """
    Knocks out the faction this warrior led, if he led one.

    Most warriors are nobody's leader, so the usual answer is None. "Faction.leader" is looked up
    rather than "warrior.faction" because capture clears the latter before this runs - the leader
    relation is the only remaining record of who led whom.
    """
    faction = (
        Faction.objects.still_in_play(savegame_id=context.warrior.savegame_id).filter(leader=context.warrior).first()
    )

    if faction is None:
        return None

    faction.is_defeated = True
    faction.save(update_fields=("is_defeated",))

    return FactionWasDefeated(faction=faction, savegame=faction.savegame)


@message_registry.register_command(command=SetNewLeaderWarrior)
def handle_set_new_leader_warrior(*, context: SetNewLeaderWarrior) -> list[Event] | Event:
    context.faction.leader = context.warrior
    context.faction.save()

    return NewLeaderWarriorSet(faction=context.faction, warrior=context.warrior)


@message_registry.register_command(command=EarnMoneyFromBuildings)
def handle_earn_money_from_buildings(*, context: EarnMoneyFromBuildings) -> list[Event] | Event:
    # Get hall building
    hall_type = context.faction.town.hall
    hall_building = Hall.get_building_by_type(building_type=hall_type)

    return MonthlyBuildingMoneyEarned(
        faction=context.faction,
        amount=hall_building.REVENUE_PER_ROUND,
        month=context.month,
    )
