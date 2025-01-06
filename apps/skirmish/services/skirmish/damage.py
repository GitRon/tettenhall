from apps.core.event_loop.messages import Event
from apps.skirmish.choices.skirmish_action import SkirmishActionTypeHint
from apps.skirmish.messages.events.warrior import WarriorDefendedAllDamage, WarriorTookDamage
from apps.skirmish.models import Skirmish, Warrior
from apps.skirmish.services.actions.utils import get_service_by_attack_action


class SkirmishDamageService:
    skirmish: Skirmish
    message_list: list[Event]

    attacker: Warrior
    attack_action: SkirmishActionTypeHint

    defender: Warrior
    defender_action: SkirmishActionTypeHint

    def __init__(
        self,
        *,
        skirmish: Skirmish,
        attacker: Warrior,
        attacker_action: SkirmishActionTypeHint,
        defender: Warrior,
        defender_action: SkirmishActionTypeHint,
    ):
        self.skirmish = skirmish
        self.message_list = []

        self.attacker = attacker
        self.attack_action = attacker_action

        self.defender = defender
        self.defender_action = defender_action

    def _deal_damage(self, *, attack: int, defense: int) -> int:
        damage = max(attack - defense, 0)

        if damage > 0:
            self.message_list.append(
                WarriorTookDamage(
                    WarriorTookDamage.Context(
                        skirmish=self.skirmish,
                        attacker=self.attacker,
                        attacker_damage=attack,
                        defender=self.defender,
                        defender_damage=defense,
                        damage=damage,
                    )
                )
            )
        else:
            self.message_list.append(
                WarriorDefendedAllDamage(
                    WarriorDefendedAllDamage.Context(
                        skirmish=self.skirmish,
                        attacker=self.attacker,
                        defender=self.defender,
                        attacker_damage=attack,
                        defender_damage=defense,
                    )
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
