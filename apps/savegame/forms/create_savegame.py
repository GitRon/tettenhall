from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Fieldset, Layout, Submit
from django import forms

from apps.faction.models import Culture


class SavegameCreateForm(forms.Form):
    town_name = forms.CharField(label="Town Name", max_length=100)
    faction_name = forms.CharField(label="Faction Name", max_length=100)
    faction_culture = forms.ModelChoiceField(label="Faction culture", queryset=Culture.objects.all())

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "",
                Div(Field("town_name", css_class="uk-input"), css_class="uk-margin"),
                Div(Field("faction_name", css_class="uk-input"), css_class="uk-margin"),
                Div(Field("faction_culture", css_class="uk-select"), css_class="uk-margin"),
                Div(
                    Submit(
                        "submit",
                        "Create savegame",
                        css_class="uk-button uk-button-primary uk-button-small",
                    )
                ),
            )
        )

        super().__init__(*args, **kwargs)
