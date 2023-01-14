from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms

from apps.skirmish.models.warrior import FightAction


class SkirmishWarriorRoundActionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        faction_id = kwargs.pop("faction_id", None)
        warrior_id = kwargs.pop("warrior_id", None)

        field_name = f"warrior-fight-action[{faction_id}][{warrior_id}]"
        # todo die daten muss ich per parser noch verarbeiten, aber wie?

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field(field_name, css_class="uk-select")),
        )

        super().__init__(*args, **kwargs)

        self.fields[field_name] = forms.ChoiceField(
            label="", choices=FightAction.TypeChoices.choices, initial=FightAction.TypeChoices.SIMPLE_ATTACK
        )
