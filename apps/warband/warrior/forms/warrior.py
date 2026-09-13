from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.template.defaultfilters import floatformat
from django.urls import reverse

from apps.common import form_styles
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
    #: The man this slot belongs to, so an option can tell "somebody else has it" from "you have it".
    #: Set by the form, because the field is built before there is an instance to ask.
    wearer: Warrior | None = None

    def label_from_instance(self, obj: Item) -> str:  # noqa: PBR001
        """
        The item, its dice, what those dice average - and who has to give it up for this.

        "__str__" carries the name and the notation already, and the mean is what tells a rusty
        battle axe from a traditional spear: "1d6+1" and "2d4" are two strings a player has to do
        arithmetic on. The item's own mean rather than this warrior's, so the options rank the way
        the shop's cards rank; what the man in front of us makes of it is on his page, next to the
        strength that scales it.

        Whether the number is damage or protection is written out rather than left to the heading
        above, because a select option is read out on its own.

        The carrier is named because the list is no longer only what nobody is using: picking an
        option can take a sword off a man somewhere down the roster, and an option that did not say
        so would spring that on the player after the save. The slot's own man is left unnamed - he is
        the current value, and "carried by" against his own name reads as a second person.
        """
        measure = "damage" if obj.is_weapon else "protection"
        label = f"{obj} - {floatformat(obj.expectancy_value)} {measure} on average"

        carrier = obj.worn_by
        if carrier is not None and carrier != self.wearer:
            label = f"{label}, carried by {carrier.display_name}"

        return label


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
            Div(Field(htmx_field, css_class=form_styles.SELECT)),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class=form_styles.BUTTON_PRIMARY_SMALL,
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

        # Everything of the right kind the faction owns, whether or not somebody is carrying it.
        #
        # Offering only the spare ones is what forced a cascade to be walked in one order and never
        # said so: moving a sword from the best man to the second meant re-equipping the best man
        # first to release it, and a player who started at the second saw a list without the sword he
        # was trying to move and no way to learn why. Picking an item somebody holds is a swap, which
        # "EquipItem" settles - see the handler for why both rows have to be written together.
        self.fields[htmx_field].queryset = Item.objects.filter(
            type__function=SLOT_FUNCTIONS[htmx_field],
            owner_id=self.instance.faction,
        ).select_related("type", "warrior_weapon", "warrior_armor")

        # The option labels ask every item who is carrying it, and the reverse one-to-ones above are
        # what keeps that to the one query the select already costs
        self.fields[htmx_field].wearer = self.instance

    def _post_clean(self) -> None:
        """
        Deliberately builds no instance, because this form no longer writes one.

        A bound ModelForm assigns the cleaned value to "self.instance", and Django's one-to-one
        descriptor writes the reverse of that assignment onto the item as well, to save a query
        later. That reverse is a lie until the save happens: the item would name the man who is
        about to receive it as the man already carrying it, and "handle_equip_item" - which reads
        exactly that to find out whose hands it is coming out of - would swap the receiver with
        himself and hand him back what he was holding.

        The choice is validated by the field's own queryset, which is the whole of what this form is
        for. "EquipItem" does the writing.
        """
