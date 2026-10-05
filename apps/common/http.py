from django.http import HttpResponse

# What a view says when its command did not go through and no refusal can name a reason any more: an
# overlapping request changed the state first, so the page the click was made on is out of date
STALE_PAGE_NOTICE = "That did not go through - something changed first. Have another look."


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
