from django.views import generic


class DashboardView(generic.TemplateView):
    template_name = "account/dashboard.html"
