"""
Tests for base.html, which every authenticated page extends.

Nothing that breaks here is confined to one view. A template error turns the whole site into a 500
for the affected user, which is why the status code alone is worth asserting; a broken inline script
block disarms every htmx control on the page, silently.
"""

import pytest
from django.contrib import messages
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_renders_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The navbar reverses the faction and town-square urls from "current_savegame.player_faction_id".
    A savegame can exist before its faction does, and reversing either with an empty id raises
    NoReverseMatch - so every authenticated page answered 500.
    """
    response = logged_in_client.get(reverse("account:dashboard-view"))

    assert response.status_code == 200


def test_message_with_a_quote_stays_inside_the_javascript_string_literal():
    """
    Deliberate exception to "never assert on rendered HTML" (testing-strategy.md): this defect lives
    only in the rendered output, so status and context are identical with and without it.

    A message is interpolated into a JavaScript string literal. One holding a double quote used to
    close that literal early, and a SyntaxError is a parse error - the browser threw away the whole
    inline block, which is also where the CSRF header, the notification listener and the 5xx toast are
    registered. Every htmx control on the landing page then posted without a token and got a 403.
    """
    content = render_to_string(
        "base.html", {"messages": [Message(messages.SUCCESS, 'You accepted the quest "Pillage village".')]}
    )

    assert '"Pillage village"' not in content
    # the JavaScript escaping of &quot;Pillage village&quot; - a quote that never reaches the literal
    assert "\\u0026quot\\u003BPillage village\\u0026quot\\u003B" in content


def test_message_with_angle_brackets_reaches_the_toast_as_text():
    """
    The same exception, for the sink underneath: UIkit inserts "message" as HTML rather than as text,
    so escaping for the JavaScript literal alone would still let a message be parsed as markup.
    """
    content = render_to_string("base.html", {"messages": [Message(messages.SUCCESS, "A raid on <the moor>.")]})

    # < would satisfy the JavaScript parser and still hand UIkit a "<" to open a tag with
    assert "\\u003Cthe moor" not in content
    # the JavaScript escaping of &lt;the moor&gt;
    assert "\\u0026lt\\u003Bthe moor\\u0026gt\\u003B" in content
