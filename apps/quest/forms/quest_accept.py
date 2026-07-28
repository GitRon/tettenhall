from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms

from apps.faction.models import Faction
from apps.quest.models.quest import Quest
from apps.quest.models.quest_contract import QuestContract
from apps.skirmish.models.warrior import Warrior


class QuestAcceptForm(forms.ModelForm):
    class Meta:
        model = QuestContract
        fields = ("faction", "quest", "assigned_warriors")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(Field("faction"), Field("quest")),
            Div(Field("assigned_warriors", css_class="uk-select")),
            Div(
                Submit(
                    "submit",
                    "Accept quest",
                    css_class="uk-button uk-button-primary uk-button-small",
                )
            ),
        )

        quest_id = kwargs.pop("quest_id")
        player_faction_id = kwargs.pop("player_faction_id")

        super().__init__(*args, **kwargs)

        # Both fields are hidden inputs, so their querysets have to do the validating: left at the
        # default "everything" a hand-edited value would name another player's quest or faction
        quest_qs = Quest.objects.filter(id=quest_id)
        quest = quest_qs.first()
        self.fields["quest"].queryset = quest_qs
        self.fields["quest"].initial = quest
        self.fields["quest"].widget = forms.HiddenInput()

        faction_qs = Faction.objects.filter(id=player_faction_id)
        faction = faction_qs.get()
        self.fields["faction"].queryset = faction_qs
        self.fields["faction"].initial = faction
        self.fields["faction"].widget = forms.HiddenInput()

        # TODO: this is buggy, i've accepted a quest, not started it and i can select all warriors for the second
        #  quest in the same round
        self.fields["assigned_warriors"].queryset = (
            Warrior.objects.filter_healthy()
            .filter(
                faction=faction,
            )
            .exclude_currently_busy(month=quest.target_faction.savegame.current_month)
            .distinct()
        )
