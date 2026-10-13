from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.choices.posting import PostingChoices
from apps.warband.warrior.services.postings import PlaceStanding

POSTING_SUMMARY_TAG = '<c-faction.posting-summary :places="places" />'


def test_posting_summary_reads_each_place_with_its_count_in_the_order_given():
    places = [
        PlaceStanding(posting=PostingChoices.BURH, label="Burh", standing_count=6),
        PlaceStanding(posting=PostingChoices.VILLAGE, label="Village", standing_count=2),
        PlaceStanding(posting=PostingChoices.HERDS, label="Herds", standing_count=0),
    ]

    html = render_component(tag=POSTING_SUMMARY_TAG, context={"places": places})

    assert " ".join(parse(html).get_text(" ").split()) == "Burh 6 · Village 2 · Herds 0"
