"""
Tests for base.html, which every authenticated page extends.

Nothing that breaks here is confined to one view. A template error turns the whole site into a 500
for the affected user, which is why the status code alone is worth asserting; and the toast sink below
is where names the game generated - factions, towns, warriors, quests - are read either as words or as
markup.
"""

import pytest
from django.contrib import messages
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_renders_without_a_player_faction(logged_in_client, savegame_without_player_faction):
    """
    The navbar reverses the faction and town-square urls from "current_savegame.player_faction_id".
    A savegame can exist before its faction does, and reversing either with an empty id raises
    NoReverseMatch - so every authenticated page answered 500.
    """
    response = logged_in_client.get(reverse("warband:dashboard-view"))

    assert response.status_code == 200


def test_message_with_a_quote_travels_as_a_document_node():
    """
    Deliberate exception to "never assert on rendered HTML" (testing-strategy.md): this defect lives
    only in the rendered output, so status and context are identical with and without it.

    A message is rendered into a "template" element and read back by "static/js/tettenhall.js" with
    "textContent". The element is the whole safety argument: autoescaping handles the value on the way
    in, so a quote is markup-escaped rather than left to end a string literal, and there is no script
    literal for it to end.
    """
    content = render_to_string(
        "base.html", {"messages": [Message(messages.SUCCESS, 'You accepted the quest "Pillage village".')]}
    )

    assert '"Pillage village"' not in content
    assert "&quot;Pillage village&quot;" in content
    # No message reaches JavaScript as source any more. This is what would break first if the sink
    # moved back into a literal.
    assert "UIkit.notification" not in content


def test_message_with_angle_brackets_reaches_the_toast_as_text():
    """
    The same exception, for the markup half: the value sits in a document node, so a "<" that arrived
    unescaped would open a tag inside the template element and the toast would read whatever survived.
    """
    content = render_to_string("base.html", {"messages": [Message(messages.SUCCESS, "A raid on <the moor>.")]})

    assert "<the moor>" not in content
    assert "&lt;the moor&gt;" in content


@override_settings(MESSAGE_TAGS={messages.SUCCESS: 'success" onload="alert(1)'})
def test_message_level_tag_is_escaped_for_the_attribute_it_sits_in():
    """
    The level tag is an attribute value on the same element, which is its own sink: a quote there ends
    the attribute and everything after it is read as more attributes. Nothing in this project overrides
    MESSAGE_TAGS, so the vocabulary is fixed and harmless today - which is exactly why the escaping
    would be dropped by someone tidying up without anything failing.
    """
    content = render_to_string("base.html", {"messages": [Message(messages.SUCCESS, "A quiet month.")]})

    assert 'onload="alert(1)"' not in content
    assert 'data-level="success&quot; onload=&quot;alert(1)"' in content
