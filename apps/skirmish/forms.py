from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.urls import reverse

from apps.skirmish.models.skirmish import SkirmishWarriorRoundAction


class SkirmishWarriorRoundActionForm(forms.ModelForm):
    class Meta:
        model = SkirmishWarriorRoundAction
        fields = ("skirmish", "warrior", "round", "action")

    def __init__(self, *args, **kwargs):
        skirmish_id = kwargs.pop("skirmish_id", None)
        warrior_id = kwargs.pop("warrior_id", None)
        skirmish_round = kwargs.pop("round", None)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            "skirmish:warrior-skirmish-round-action-create-htmx",
            args=(skirmish_id, warrior_id, skirmish_round),
        )
        self.helper.attrs = {"hx-post": self.helper.form_action}
        self.helper.layout = Layout(
            Div("skirmish", "warrior", "round", css_class="uk-hidden"),
            Div(Field("action", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Save",
                    css_class="uk-button uk-button-primary uk-button-small",
                ),
                css_class="uk-margin",
            ),
        )

        super().__init__(*args, **kwargs)

        self.fields["skirmish"].widget = forms.HiddenInput()
        self.fields["skirmish"].initial = skirmish_id

        self.fields["warrior"].widget = forms.HiddenInput()
        self.fields["warrior"].initial = warrior_id

        self.fields["round"].widget = forms.HiddenInput()
        self.fields["round"].initial = skirmish_round

        self.fields["action"].empty_label = None
        self.fields["action"].label = ""
