import json
from http import HTTPStatus

from django.http import HttpResponse
from django.urls import reverse
from django.views import generic
from queuebie.runner import handle_message

from apps.common.http import hx_redirect
from apps.warband.month.messages.commands.month import PrepareMonth
from apps.warband.savegame.mixins import RunningSavegameRequiredMixin
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request
from apps.warband.skirmish.models import Skirmish


class FinishMonthView(RunningSavegameRequiredMixin, generic.View):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        # Fetch current savegame record
        current_savegame: Savegame = get_current_savegame_for_request(request=request)
        if current_savegame is None:
            return HttpResponse(status=HTTPStatus.NOT_FOUND)

        # Every fight is settled in the month it was started. This refusal is what makes that true -
        # nothing the month advance raises starts a fight - so the availability rules and the training
        # run may take every open skirmish to be this month's
        if Skirmish.objects.unresolved().for_savegame(savegame_id=current_savegame.id).exists():
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps(
                {
                    "notification": "Please resolve all open skirmishes before you finish this month.",
                }
            )
            return response

        # The button posts the month it was rendered in. A request for any other month comes from a
        # page the month has already moved past - the second of a double click, or a stale tab - and
        # finishing "the current month" for it would run a month the player never looked at.
        try:
            posted_month = int(request.POST["month"])
        except KeyError, ValueError:
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)

        if posted_month != current_savegame.current_month:
            return hx_redirect(url=reverse("warband:dashboard-view"))

        handle_message(
            PrepareMonth(
                savegame=current_savegame,
                month=posted_month,
            )
        )

        return hx_redirect(url=reverse("warband:dashboard-view"))
