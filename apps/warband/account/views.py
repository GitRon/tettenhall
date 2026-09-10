from ambient_toolbox.view_layer.views import RequestInFormKwargsMixin
from django.contrib.auth import login, logout, user_login_failed
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from apps.warband.account.forms.login import LoginForm
from apps.warband.month.models.player_month_log import PlayerMonthLog
from apps.warband.month.services.player_month_log import group_player_month_logs
from apps.warband.savegame.models.savegame import Savegame
from apps.warband.savegame.services.current_savegame import get_current_savegame_for_request


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
    pattern_name = "warband:login-view"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


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
            # Only set once the game has been decided, so the template can ask a single question
            # instead of comparing against the running value itself
            if current_savegame.is_over:
                context["savegame_outcome"] = current_savegame.get_outcome_display()

        return context
