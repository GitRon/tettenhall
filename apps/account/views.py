from ambient_toolbox.view_layer.views import RequestInFormKwargsMixin
from django.contrib.auth import login, logout, user_login_failed
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
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
