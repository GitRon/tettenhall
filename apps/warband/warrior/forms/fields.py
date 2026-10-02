from django import forms

from apps.warband.skirmish.models.warrior import Warrior


class WarriorMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    A pick of men, each offered by his full name.

    The default label is "__str__", the bare name, which leaves the player sending "Uthred" somewhere
    without seeing that Uthred is his Ealdorman, or which of two men called Wulf is the strong one.

    Naming him asks whether he holds his faction's seat, so the queryset handed in brings the faction
    along with the men - see [Warrior.is_leader].
    """

    def label_from_instance(self, obj: Warrior) -> str:  # noqa: PBR001
        return obj.display_name
