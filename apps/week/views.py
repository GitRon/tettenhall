import json

from django.db.models import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.savegame.models.savegame import Savegame
from apps.week.messages.commands.week import PrepareWeek
from apps.week.models.player_week_log import PlayerWeekLog


class FinishWeekView(generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=request.user.id)

        handle_message(
            PrepareWeek(
                PrepareWeek.Context(
                    savegame=current_savegame,
                )
            )
        )

        response = HttpResponse(status=200)
        response["HX-Redirect"] = reverse("account:dashboard-view")
        return response


class PlayerWeekLogListView(generic.ListView):
    model = PlayerWeekLog
    template_name = "player-week-log/components/player_week_log_list.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().for_user(user_id=self.request.user.id)


class AcknowledgePlayerWeekLogView(generic.DeleteView):
    model = PlayerWeekLog
    http_method_names = ("delete",)

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().for_user(user_id=self.request.user.id)

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        # TODO: add some validation when we have save games

        super().delete(request, *args, **kwargs)

        response = HttpResponse(status=202)
        response["HX-Trigger"] = json.dumps(
            {
                "loadMessageList": "-",
            }
        )
        return response

    def get_success_url(self) -> None:
        return None
