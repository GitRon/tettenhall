from ambient_toolbox.view_layer.views import RequestInFormKwargsMixin
from axes.handlers.proxy import AxesProxyHandler
from django.contrib.auth import login, logout, user_login_failed
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from apps.account.forms.login import LoginForm
from apps.month.models.player_month_log import PlayerMonthLog
from apps.savegame.models.savegame import Savegame


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

        current_savegame: Savegame = Savegame.objects.get_current_savegame(user_id=self.request.user.id)

        if current_savegame:
            context["player_month_logs"] = PlayerMonthLog.objects.for_savegame(
                savegame_id=current_savegame.id
            ).order_by("-month")
            context["faction"] = current_savegame.player_faction

        return context
