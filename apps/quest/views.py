import json

from django.http import HttpResponse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin

from apps.core.event_loop.runner import handle_message
from apps.quest.messages.commands.quest import AcceptQuest
from apps.quest.models.quest import Quest


class QuestAcceptView(SingleObjectMixin, generic.View):
    model = Quest
    http_method_names = ("post",)

    def post(self, *args, **kwargs):
        obj = self.get_object()

        # todo we need a form here to select which warriors we want to send on this quest

        handle_message(AcceptQuest.generator(context_data={"quest": obj}))

        response = HttpResponse(status=200)
        response["HX-Trigger"] = json.dumps(
            {
                "loadFactionItemList": "-",
                "loadFactionWarriorList": "-",
            }
        )
        return response
