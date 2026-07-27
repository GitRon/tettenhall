import json
from http import HTTPStatus

from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.month.messages.commands.month import PrepareMonth
from apps.month.models.player_month_log import PlayerMonthLog
from apps.savegame.mixins import SavegameScopedQuerysetMixin
from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Skirmish


class FinishMonthView(generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)
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

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response


class PlayerMonthLogListView(SavegameScopedQuerysetMixin, generic.ListView):
    model = PlayerMonthLog
    template_name = "player-month-log/components/player_month_log_list.html"


class AcknowledgePlayerMonthLogView(SavegameScopedQuerysetMixin, generic.DeleteView):
    model = PlayerMonthLog
    http_method_names = ("delete",)

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        super().delete(request, *args, **kwargs)

        response = HttpResponse(status=HTTPStatus.ACCEPTED)
        response["HX-Trigger"] = json.dumps(
            {
                "loadMessageList": "-",
            }
        )
        return response

    def get_success_url(self) -> None:
        return None
