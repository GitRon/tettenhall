from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.db.models import Q
from django.template.defaultfilters import floatformat
from django.urls import reverse

from apps.warband.item.models.item import Item
from apps.warband.item.models.item_type import ItemType
from apps.warband.skirmish.models.warrior import Warrior

# The item function each gear slot may be filled from, and by being that, the list of slots this form
# will build at all. One mapping rather than a tuple of names beside it: a slot the form cannot say
# what belongs in is a slot it has no business rendering, and the view's own allowlist reads the same
# names back out of "Meta.fields"
SLOT_FUNCTIONS = {
    "weapon": ItemType.FunctionChoices.FUNCTION_WEAPON,
    "armor": ItemType.FunctionChoices.FUNCTION_ARMOR,
}


class ItemChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Item) -> str:  # noqa: PBR001
        """
        The item, its dice and what those dice average - the figure the choice actually turns on.

        "__str__" carries the name and the notation already, and the mean is what tells a rusty
        battle axe from a traditional spear: "1d6+1" and "2d4" are two strings a player has to do
        arithmetic on. The item's own mean rather than this warrior's, so the options rank the way
        the shop's cards rank; what the man in front of us makes of it is on his page, next to the
        strength that scales it.

        Whether the number is damage or protection is written out rather than left to the heading
        above, because a select option is read out on its own.
        """
        measure = "damage" if obj.is_weapon else "protection"

        return f"{obj} - {floatformat(obj.expectancy_value)} {measure} on average"


class WarriorForm(forms.ModelForm):
    class Meta:
        model = Warrior
        fields = tuple(SLOT_FUNCTIONS)
        # Both slots hold an item, so both are offered with the item's figures on the option
        field_classes = dict.fromkeys(SLOT_FUNCTIONS, ItemChoiceField)

    def __init__(self, *args, **kwargs):
        # Ensure that only allowed fields can be rendered
        htmx_field = kwargs.pop("htmx_field", None)
        htmx_field = htmx_field if htmx_field in self.Meta.fields else None

        if htmx_field is None:
            raise RuntimeError("Badly configured HTMX form")

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-post": reverse(
                "warband:warrior-partial-update-view",
                kwargs={"pk": kwargs["instance"].id, "htmx_attribute": htmx_field},
            ),
            "hx-target": f"#partial-field-container-{htmx_field}",
            "hx-swap": "outerHTML",
        }
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field(htmx_field, css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class="uk-button uk-button-primary uk-button-small",
                )
            ),
        )

        super().__init__(*args, **kwargs)

        # One slot per request, so the form is built down to it rather than built whole and then
        # covered up. A field that is gone is not rendered, not posted and not written back: what the
        # warrior carries in the other hand survives the save because nothing here has an opinion
        # about it
        self.fields = {htmx_field: self.fields[htmx_field]}
        self.fields[htmx_field].label = ""

        # What the faction has spare, plus what this warrior is already carrying - the slot's own
        # item would otherwise be missing from the list that is supposed to contain the current value
        equipped_relation = f"warrior_{htmx_field}"
        self.fields[htmx_field].queryset = Item.objects.filter(
            Q(**{f"{equipped_relation}__isnull": True}) | Q(**{equipped_relation: self.instance}),
            type__function=SLOT_FUNCTIONS[htmx_field],
            owner_id=self.instance.faction,
        )
