from ambient_toolbox.view_layer.views import RequestInFormKwargsMixin
from axes.handlers.proxy import AxesProxyHandler
from django.contrib.auth import login, logout, user_login_failed
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from apps.account.forms.login import LoginForm
from apps.faction.models.faction import Faction
from apps.week.models.player_week_log import PlayerWeekLog


class LoginView(RequestInFormKwargsMixin, generic.FormView):
    template_name = "account/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("account:dashboard-view")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        if AxesProxyHandler.is_locked(request):
            return HttpResponseForbidden("Too many access attempt. Please try again later.")

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
    pattern_name = "account:login-view"

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)


class DashboardView(generic.TemplateView):
    template_name = "account/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: query for current savegame
        context["player_week_logs"] = PlayerWeekLog.objects.all()
        # TODO: get from current savegame
        context["faction"] = Faction.objects.get(id=2)
        return context
