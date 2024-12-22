import json

from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.core.event_loop.runner import handle_message
from apps.quest.forms.quest_accept import QuestAcceptForm
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.models.quest import Quest


class QuestListView(generic.ListView):
    model = Quest
    template_name = "quest/quest_list.html"

    def get_queryset(self):
        return super().get_queryset().filter(faction=2)


class QuestDetailView(SingleObjectMixin, generic.FormView):
    model = Quest
    form_class = QuestAcceptForm
    template_name = "quest/quest_detail.html"
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["quest_id"] = self.object.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        return context

    def get_queryset(self):
        return super().get_queryset().filter(faction=2)


class QuestAcceptView(SingleObjectMixin, generic.View):
    model = Quest
    http_method_names = ("post",)

    def post(self, *args, **kwargs):
        obj = self.get_object()

        # todo we need a form here to select which warriors we want to send on this quest -> QuestDetailView

        handle_message(AcceptQuest.generator(context_data={"quest": obj}))

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response
