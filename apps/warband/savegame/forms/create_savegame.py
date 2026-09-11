from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Fieldset, Layout, Submit
from django import forms

from apps.common import form_styles
from apps.warband.faction.models import Culture


class SavegameCreateForm(forms.Form):
    town_name = forms.CharField(label="Town Name", max_length=100)
    faction_name = forms.CharField(label="Faction Name", max_length=100)
    faction_culture = forms.ModelChoiceField(
        label="Faction culture",
        queryset=Culture.objects.all(),
        # The one choice on this form that cannot be taken back, and the only honest thing to say
        # about it today: perks are not implemented, so the tongue is all it decides.
        help_text="The tongue your own men are named in. It decides nothing else, for now.",
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "",
                Div(Field("town_name", css_class=form_styles.INPUT), css_class=form_styles.FIELD_SPACING),
                Div(Field("faction_name", css_class=form_styles.INPUT), css_class=form_styles.FIELD_SPACING),
                Div(Field("faction_culture", css_class=form_styles.SELECT), css_class=form_styles.FIELD_SPACING),
                Div(
                    Submit(
                        "submit",
                        "Create savegame",
                        css_class=form_styles.BUTTON_PRIMARY_SMALL,
                    )
                ),
            )
        )

        super().__init__(*args, **kwargs)
