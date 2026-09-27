import json
from http import HTTPStatus

from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from queuebie.runner import handle_message

from apps.common.http import hx_redirect
from apps.warband.incident.incidents import INCIDENTS_BY_NAME
from apps.warband.incident.messages.commands.pending_incident import AnswerPendingIncident
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.incident.services.pending_incident import get_pending_incident_answer_refusal
from apps.warband.savegame.mixins import PlayerFactionScopedQuerysetMixin, RunningSavegameRequiredMixin
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


class PendingIncidentAnswerView(
    RunningSavegameRequiredMixin, PlayerFactionScopedQuerysetMixin, SingleObjectMixin, generic.View
):
    """
    Answers one question the world put to the player, whichever entry asked it.

    The view knows nothing about any single incident: the entry declares its options, and the posted
    key is checked against them before anything is dispatched. A key naming no option is a request
    nobody's page offered, so it is a 400 rather than a notification.
    """

    model = PendingIncident
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        pending_incident = self.get_object()

        option = INCIDENTS_BY_NAME[pending_incident.incident].get_option(key=request.POST.get("option", ""))
        if option is None:
            return HttpResponseBadRequest()

        refusal = get_pending_incident_answer_refusal(pending_incident=pending_incident, option=option)
        if refusal is not None:
            response = HttpResponse(status=HTTPStatus.NO_CONTENT)
            response["HX-Trigger"] = json.dumps({"notification": refusal})
            return response

        current_savegame = get_current_savegame_for_request(request=request)
        handle_message(
            AnswerPendingIncident(
                pending_incident=pending_incident,
                option=option,
                month=current_savegame.current_month,
            )
        )

        return hx_redirect(url=reverse("warband:dashboard-view"))
