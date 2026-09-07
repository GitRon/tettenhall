from django.http import HttpResponse


def hx_redirect(*, url: str) -> HttpResponse:
    """
    An empty response telling htmx to leave the page for "url".

    The redirect has to ride on a header rather than a 302: htmx swaps whatever a request answers
    with into the target element, so a redirect the browser follows would land a whole page inside a
    fragment.
    """
    response = HttpResponse()
    response["HX-Redirect"] = url

    return response
