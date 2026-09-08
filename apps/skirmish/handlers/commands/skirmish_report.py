from queuebie import message_registry
from queuebie.messages import Event

from apps.skirmish.messages.commands.skirmish_report import (
    RecordSkirmishBlow,
    RecordSkirmishCasualty,
    RecordSkirmishSpoil,
    RecordWarriorGrowth,
)
from apps.skirmish.messages.events.skirmish_report import (
    SkirmishBlowRecorded,
    SkirmishCasualtyRecorded,
    SkirmishSpoilRecorded,
    WarriorGrowthRecorded,
)
from apps.skirmish.models import SkirmishBlow, SkirmishCasualty, SkirmishSpoil, SkirmishWarriorGrowth


@message_registry.register_command(command=RecordSkirmishSpoil)
def handle_record_skirmish_spoil(*, context: RecordSkirmishSpoil) -> Event:
    spoil = SkirmishSpoil.objects.create_record(
        skirmish=context.skirmish,
        faction=context.faction,
        kind=context.kind,
        item=context.item,
        warrior=context.warrior,
        amount=context.amount,
        description=context.description,
    )

    return SkirmishSpoilRecorded(spoil=spoil)


@message_registry.register_command(command=RecordWarriorGrowth)
def handle_record_warrior_growth(*, context: RecordWarriorGrowth) -> Event:
    # Which side the man fought on is a query, so it is answered here rather than carried on the
    # command - the event handlers raising it are not allowed to run one
    growth = SkirmishWarriorGrowth.objects.record_growth(
        skirmish=context.skirmish,
        warrior=context.warrior,
        faction=context.warrior.faction,
        gained_experience=context.gained_experience,
        reached_level=context.reached_level,
        gained_strength=context.gained_strength,
        gained_dexterity=context.gained_dexterity,
        gained_max_health=context.gained_max_health,
        gained_max_morale=context.gained_max_morale,
        new_monthly_salary=context.new_monthly_salary,
    )

    return WarriorGrowthRecorded(growth=growth)


@message_registry.register_command(command=RecordSkirmishCasualty)
def handle_record_skirmish_casualty(*, context: RecordSkirmishCasualty) -> Event:
    casualty = SkirmishCasualty.objects.record_casualty(
        skirmish=context.skirmish,
        warrior=context.warrior,
        fate=context.fate,
    )

    return SkirmishCasualtyRecorded(casualty=casualty)


@message_registry.register_command(command=RecordSkirmishBlow)
def handle_record_skirmish_blow(*, context: RecordSkirmishBlow) -> Event:
    blow = SkirmishBlow.objects.create_record(
        skirmish=context.skirmish,
        round_number=context.round_number,
        attacker=context.attacker,
        attacker_action=context.attacker_action,
        defender=context.defender,
        defender_action=context.defender_action,
        outcome=context.outcome,
        attack=context.attack,
        defense=context.defense,
        damage=context.damage,
    )

    return SkirmishBlowRecorded(blow=blow)
