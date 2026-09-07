import json
from http import HTTPStatus

from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.common.http import hx_redirect
from apps.month.messages.commands.month import PrepareMonth
from apps.savegame.mixins import RunningSavegameRequiredMixin
from apps.savegame.models.savegame import Savegame
from apps.savegame.services.current_savegame import get_current_savegame_for_request
from apps.skirmish.models import Skirmish


class FinishMonthView(RunningSavegameRequiredMixin, generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        current_savegame: Savegame = get_current_savegame_for_request(request=request)
        if current_savegame is None:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        # If we have unresolved skirmishes, we can't finish the round
        if Skirmish.objects.unresolved().for_savegame(savegame_id=current_savegame.id).exists():
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps(
                {
                    "notification": "Please resolve all open skirmishes before you finish this month.",
                }
            )
            return response

        handle_message(
            PrepareMonth(
                savegame=current_savegame,
            )
        )

        return hx_redirect(url=reverse("account:dashboard-view"))
