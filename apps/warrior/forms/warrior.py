from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.db.models import Q
from django.forms import HiddenInput
from django.urls import reverse

from apps.item.models.item import Item
from apps.item.models.item_type import ItemType
from apps.skirmish.models.warrior import Warrior


class WarriorForm(forms.ModelForm):
    class Meta:
        model = Warrior
        fields = ("weapon", "armor")

    def __init__(self, *args, **kwargs):
        # Ensure that only allowed fields can be rendered
        # todo would be nicer to replace the original fields
        htmx_field = kwargs.pop("htmx_field", None)
        htmx_field = htmx_field if htmx_field in self.Meta.fields else None

        if htmx_field is None:
            raise RuntimeError("Badly configured HTMX form")

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-post": reverse(
                "warrior:warrior-partial-update-view",
                kwargs={"pk": kwargs["instance"].id, "htmx_attribute": htmx_field},
            ),
            "hx-target": f"#partial-field-container-{htmx_field}",
            "hx-swap": "outerHTML",
        }
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("weapon", css_class="uk-select")),
            Div(Field("armor", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class="uk-button uk-button-primary uk-button-small",
                )
            ),
        )

        super().__init__(*args, **kwargs)

        # Populate querysets
        self.fields["weapon"].queryset = Item.objects.filter(
            Q(warrior_weapon__isnull=True) | Q(warrior_weapon=self.instance),
            type__function=ItemType.FunctionChoices.FUNCTION_WEAPON,
            owner_id=self.instance.faction,
        )
        self.fields["armor"].queryset = Item.objects.filter(
            Q(warrior_armor__isnull=True) | Q(warrior_armor=self.instance),
            type__function=ItemType.FunctionChoices.FUNCTION_ARMOR,
            owner_id=self.instance.faction,
        )

        for _field_name, _field in self.fields.items():
            if _field_name == htmx_field:
                self.fields[_field_name].label = ""
            else:
                self.fields[_field_name].widget = HiddenInput()
                self.fields[_field_name].disabled = True
