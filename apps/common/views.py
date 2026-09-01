from django.views import generic


class ResourceBarHtmxView(generic.TemplateView):
    """
    Re-renders the navbar's three counters after an action has moved one of them.

    Read-only, so it deliberately carries no scoping mixin and no RunningSavegameRequiredMixin: it
    resolves nothing by id, and a finished savegame still has a navbar. Everything it shows comes from
    the context processors that run on every authenticated render, which is why there is no
    get_context_data here - and why they are the ones that answer for a user with no savegame yet.
    """

    template_name = "common/components/resource_bar.html"
