from apps.common.tests.html import parse, render_component
from apps.warband.calendar.date import CalendarDate
from apps.warband.warrior.projections.warrior_story import StoryEntry, WarriorStory

STORY_TAG = '<c-warrior.story :story="story" />'


def _texts(html: str, *, tag: str) -> list[str]:
    """Each element's text as a player reads it: the template wraps lines, and the newlines reach the text."""
    return [" ".join(element.get_text(" ").split()) for element in parse(html).find_all(tag)]


def test_story_says_nothing_is_written_down_for_a_man_with_no_history():
    html = render_component(tag=STORY_TAG, context={"story": WarriorStory(entries=[])})

    result = _texts(html, tag="p")

    assert result == ["Nothing he has done is written down yet."]


def test_story_dates_each_entry_and_puts_its_lines_under_it():
    when = CalendarDate.for_month(month=3, start_year=768)
    story = WarriorStory(
        entries=[
            StoryEntry(
                when=when,
                headline="Fought for Mercia against Wessex, and won",
                details=("Killed Oswy", "Reached level 3"),
                order=(3, 2, 1),
            )
        ]
    )

    html = render_component(tag=STORY_TAG, context={"story": story})

    result = _texts(html, tag="li")

    assert result == [
        f"{when.label} Fought for Mercia against Wessex, and won Killed Oswy Reached level 3",
        "Killed Oswy",
        "Reached level 3",
    ]
