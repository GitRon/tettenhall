from apps.common.http import hx_redirect


def test_hx_redirect_carries_the_target_in_the_header():
    """
    The header is the whole point: htmx swaps a response body into the target element, so a 302 the
    browser follows would land a whole page inside a fragment.
    """
    response = hx_redirect(url="/dashboard/")

    assert response.status_code == 200
    assert response["HX-Redirect"] == "/dashboard/"
