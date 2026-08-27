import random

from queuebie import message_registry
from queuebie.messages import Event

from apps.quest.messages.commands.quest import AcceptQuest, CreateNewQuest
from apps.quest.messages.events.quest import NewQuestCreated, QuestAccepted
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract
from apps.quest.services.generators.quest import QuestGenerator
from apps.skirmish.models.warrior import Warrior


@message_registry.register_command(command=CreateNewQuest)
def handle_create_new_quest(*, context: CreateNewQuest) -> list[Event] | Event | None:
    quest_generator = QuestGenerator(savegame=context.savegame)
    quest = quest_generator.process()

    # Nothing to pin to the board when every surviving rival has been flattened - see the generator
    # for why that is a quiet month rather than an error
    if quest is None:
        return None

    context.faction.available_quests.add(quest)

    return NewQuestCreated(quest=quest, faction=context.faction, month=context.month)


@message_registry.register_command(command=AcceptQuest)
def handle_accept_quest(*, context: AcceptQuest) -> list[Event] | Event:
    quest_contract = QuestContract.objects.create(
        faction=context.accepting_faction, quest=context.quest, accepted_in_month=context.month
    )
    quest_contract.assigned_warriors.add(*context.assigned_warriors)
    context.accepting_faction.active_quests.add(quest_contract)
    context.accepting_faction.available_quests.remove(quest_contract.quest)

    return QuestAccepted(
        accepting_faction=context.accepting_faction,
        target_faction=context.quest.target_faction,
        quest=context.quest,
        quest_contract=quest_contract,
        target_warriors=_muster_defenders(quest=context.quest),
        month=context.month,
    )


def _muster_defenders(*, quest: Quest) -> list[Warrior]:
    """
    Whom the target faction turns out against this errand.

    Its own war band, the way a direct attack already fields it - the difficulty decides how many of
    them show up, not how many exist. Only the ones still on their feet: a warrior who is down does
    not defend his town, and a side made up of him alone would count as beaten before the first
    round.

    Resolved here, in the command handler, because "handle_create_skirmish_for_quest_contract" reacts
    to the event this returns and may not touch the database under strict mode.

    A faction with nobody left fields nobody, and staging a fight against an empty side raises one
    hop later. What keeps that from being reachable is "Quest.objects.resolvable()", which is what
    the board and the accept view are scoped to.
    """
    healthy_warriors = list(Warrior.objects.filter_healthy().filter_faction(faction_id=quest.target_faction_id))
    minimum_turnout, maximum_turnout = quest.get_min_max_number_of_opponents()

    return random.sample(healthy_warriors, min(random.randint(minimum_turnout, maximum_turnout), len(healthy_warriors)))
