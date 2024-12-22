from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from apps.quest.models.quest import Quest
from apps.skirmish.models.warrior import Warrior


class QuestAcceptForm(forms.Form):
    quest = forms.ModelChoiceField(queryset=Quest.objects.none(), widget=forms.HiddenInput())
    warriors = forms.ModelMultipleChoiceField(label="Select warriors", queryset=Warrior.objects.none())

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("quest")),
            Div(Field("warriors", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Accept quest",
                    css_class="uk-button uk-button-primary uk-button-small",
                )
            ),
        )

        quest_id = kwargs.pop("quest_id")

        super().__init__(*args, **kwargs)

        quest_qs = Quest.objects.filter(id=quest_id)
        self.fields["quest"].queryset = quest_qs
        self.fields["quest"].initial = quest_qs.first()

        self.fields["warriors"].queryset = Warrior.objects.filter(faction=2)  # todo: exclude "busy" warriors
