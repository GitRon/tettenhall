from django import forms

from apps.warband.item.models.item import Item
from apps.warband.skirmish.models.warrior import Warrior


class AssignItemForm(forms.Form):
    """
    Which of the owning faction's men a piece of gear is being handed to.

    The select on the item card is written out in the template rather than rendered from here - the
    card needs the roster anyway to say what each man is already carrying in the slot. What this
    owns is the other half: a posted id is a free parameter, and the roster it has to be on is the
    one the item's own owner commands.
    """

    warrior = forms.ModelChoiceField(queryset=Warrior.objects.none())

    def __init__(self, *args, item: Item, **kwargs):
        super().__init__(*args, **kwargs)

        # The dead are left out the way every roster in the game leaves them out. Unowned gear - the
        # shop's shelf, and what the pub mercenaries carry - narrows to nobody rather than to every
        # faction-less warrior in the savegame, which is what "faction_id=None" would have matched.
        self.fields["warrior"].queryset = (
            Warrior.objects.none()
            if item.owner_id is None
            else Warrior.objects.exclude_dead().filter_faction(faction_id=item.owner_id)
        )
