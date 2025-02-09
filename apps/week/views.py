import json
from http import HTTPStatus

from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.savegame.models.savegame import Savegame
from apps.skirmish.models import Skirmish
from apps.week.messages.commands.week import PrepareWeek
from apps.week.models.player_week_log import PlayerWeekLog


class FinishWeekView(generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

        # If we have unresolved skirmishes, we can't finish the round
        if Skirmish.objects.unresolved().for_savegame(savegame_id=current_savegame.id).exists():
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps(
                {
                    "notification": "Please resolve all open skirmishes before you finish this week.",
                }
            )
            return response

        handle_message(
            PrepareWeek(
                savegame=current_savegame,
            )
        )

        response = HttpResponse(status=HTTPStatus.OK)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response


class PlayerWeekLogListView(generic.ListView):
    model = PlayerWeekLog
    template_name = "player-week-log/components/player_week_log_list.html"

    def get_queryset(self) -> QuerySet:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().get_queryset().for_savegame(savegame_id=current_savegame)


class AcknowledgePlayerWeekLogView(generic.DeleteView):
    model = PlayerWeekLog
    http_method_names = ("delete",)

    def get_queryset(self) -> QuerySet:
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)
        return super().get_queryset().for_savegame(savegame_id=current_savegame.id)

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
