from ambient_toolbox.view_layer.views import RequestInFormKwargsMixin
from django.contrib.auth import login, logout, user_login_failed
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from apps.warband.account.forms.login import LoginForm
from apps.warband.calendar.projections.year import YearAtAGlance
from apps.warband.incident.services.pending_incident import get_open_questions
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.month.projections.month_standing import MonthStanding
from apps.warband.month.services.player_month_log import group_player_month_logs
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request
from apps.warband.training.models.training import Training


class LoginView(RequestInFormKwargsMixin, generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("warband:dashboard-view")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())

        # No lockout check here: axes identifies the client by AXES_USERNAME_FORM_FIELD, which this
        # form does not post, so the check never matched. AxesMiddleware answers a locked-out POST
        # with AXES_LOCKOUT_TEMPLATE anyway.
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)

    def form_invalid(self, form):
        # Inform axes of failed login
        user_login_failed.send(
            sender=User, request=self.request, credentials={"username": form.cleaned_data.get("email")}
        )
        return super().form_invalid(form)


class LogoutView(generic.RedirectView):
    """
    Ends the session on a POST only. A GET is answered 405: anything that follows a link - another site's
    image tag, a browser prefetch, a crawler - would otherwise log the player out, and CSRF protection
    covers nothing but the unsafe methods.
    """

    pattern_name = "warband:login-view"
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        logout(request)
        return super().post(request, *args, **kwargs)


class DashboardView(generic.TemplateView):
    template_name = "account/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_savegame: Savegame = get_current_savegame_for_request(request=self.request)

        if current_savegame:
            # The log the player reads is his own faction's, never his savegame's, or the rivals'
            # bookkeeping joins his. A savegame without a player faction has no log of his to read yet.
            context["player_month_logs"] = group_player_month_logs(
                player_month_logs=PlayerMonthLog.objects.for_player_faction(
                    faction_id=current_savegame.player_faction_id
                )
                if current_savegame.player_faction_id
                else PlayerMonthLog.objects.none()
            )
            context["faction"] = current_savegame.player_faction
            # The training is one faction-wide row the savegame arrives with a value for, and it is
            # read rather than chosen in most months - so it is a line on the page the month begins
            # on rather than a place of its own. Every faction of the savegame owns such a row, so
            # this has to name the player's own.
            context["current_training"] = (
                Training.objects.regimen_for_faction(faction_id=current_savegame.player_faction_id)
                if current_savegame.player_faction_id
                else None
            )
            # Only set once the game has been decided, so the template can ask a single question
            # instead of comparing against the running value itself
            if current_savegame.is_over:
                context["savegame_outcome"] = current_savegame.get_outcome_display()
            else:
                # Behind the same question the banner above asks. A decided savegame keeps every
                # control it had, which is #107's to settle - and this page is where that would cost
                # the most, since "what is still open to me this month" has one answer once the game
                # is over and it is "nothing".
                #
                # Assembled here rather than in the template: ten panels each walking a relation of
                # their own is ten to thirty queries on the page every month starts on, and
                # RivalFactionListView is this codebase's standing example of answering a page's
                # questions once for the whole page instead.
                # The questions the world has put to him and he has not answered. Read with the month
                # log, which is where they are shown, but from their own rows: a question outlives
                # the log it is shown in
                context["open_questions"] = (
                    get_open_questions(faction_id=current_savegame.player_faction_id)
                    if current_savegame.player_faction_id
                    else []
                )
                month_standing = MonthStanding.for_savegame(savegame=current_savegame)
                context["month_standing"] = month_standing
                # What the months ahead will do, so the player can plan past the one he is in
                context["year_at_a_glance"] = YearAtAGlance.for_month(
                    month=current_savegame.current_month, start_year=current_savegame.start_year
                )

                if month_standing:
                    # The key the purse brief reads. It is taken off the projection rather than
                    # reimplemented, so the month page and the cost card on the ledger cannot promise
                    # different figures - the wage half of it rides in on the finance context
                    # processor either way.
                    context["building_income_amount"] = month_standing.building_income

        return context
