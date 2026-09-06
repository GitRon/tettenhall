from queuebie.messages import Event

from apps.skirmish.choices.blow_outcome import BlowOutcomeChoices
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.domain.action_roll import ActionRoll
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage, WarriorTookDamage
from apps.skirmish.models import Skirmish, Warrior
from apps.skirmish.services.actions.utils import get_service_by_attack_action


class SkirmishDamageService:
    # Roughly the share of a blow that defence cannot prevent: rounded to whole points, so it is a
    # quarter only on the way past and nothing at all below an attack of three.
    #
    # A weapon and the armour facing it are drawn from comparable dice pools, so subtracting the one
    # from the other reaches zero often, and two warriors trading blows neither can land gain morale
    # for every block and so never rout. That fight has no way to end, and an unresolved skirmish
    # holds the month open and the savegame with it.
    #
    # It answers only the fight in which blows are being thrown. Two warriors both in a defensive
    # stance throw nothing at all, this leaves their zero a zero, and the morale drain on a fully
    # defended blow is still the only thing that ends that one.
    MINIMUM_DAMAGE_SHARE = 0.25

    skirmish: Skirmish
    round_number: int
    message_list: list[Event]

    attacker: Warrior
    attack_action: SkirmishActionTypeHint

    defender: Warrior
    defender_action: SkirmishActionTypeHint

    def __init__(
        self,
        *,
        skirmish: Skirmish,
        round_number: int,
        attacker: Warrior,
        attacker_action: SkirmishActionTypeHint,
        defender: Warrior,
        defender_action: SkirmishActionTypeHint,
    ):
        self.skirmish = skirmish
        self.round_number = round_number
        self.message_list = []

        self.attacker = attacker
        self.attack_action = attacker_action

        self.defender = defender
        self.defender_action = defender_action

    def _deal_damage(self, *, attack: ActionRoll, defense: ActionRoll) -> int:
        damage = max(attack.value - defense.value, round(attack.value * self.MINIMUM_DAMAGE_SHARE))

        if damage > 0:
            self.message_list.append(
                WarriorTookDamage(
                    skirmish=self.skirmish,
                    round_number=self.round_number,
                    attacker=self.attacker,
                    attacker_action=self.attack_action,
                    attack=attack,
                    defender=self.defender,
                    defender_action=self.defender_action,
                    defense=defense,
                    damage=damage,
                )
            )
        else:
            self.message_list.append(
                WarriorDefendedAllDamage(
                    skirmish=self.skirmish,
                    round_number=self.round_number,
                    attacker=self.attacker,
                    attacker_action=self.attack_action,
                    attack=attack,
                    defender=self.defender,
                    defender_action=self.defender_action,
                    defense=defense,
                    # An action that threw nothing says so itself. Anything else that got nothing
                    # through was stopped by the armour, which is a different thing entirely and used
                    # to be recorded as the same zero
                    outcome=attack.outcome if attack.outcome is not None else BlowOutcomeChoices.OUTCOME_ABSORBED,
                )
            )

        return damage

    def process(self) -> list[Event]:
        attack_service = get_service_by_attack_action(attack_action=self.attack_action)(
            skirmish=self.skirmish, warrior=self.attacker
        )
        defend_service = get_service_by_attack_action(attack_action=self.defender_action)(
            skirmish=self.skirmish, warrior=self.defender
        )

        attack = attack_service.get_attack_value()
        defense = defend_service.get_defense_value()
        self._deal_damage(attack=attack, defense=defense)

        return self.message_list
