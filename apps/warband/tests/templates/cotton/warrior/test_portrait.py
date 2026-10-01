from apps.common.tests.html import parse, render_component
from apps.warband.skirmish.models import Warrior
from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.warrior.models.hair_colour import HairColour
from apps.warband.warrior.models.portrait_piece import PortraitPiece

PORTRAIT_TAG = '<c-warrior.portrait :warrior="warrior" frame="border border-rule" />'


def _drawn_warrior() -> Warrior:
    return WarriorFactory.build(
        portrait_face=PortraitPiece(image="img/warrior/portrait/face/01.png"),
        portrait_beard=PortraitPiece(image="img/warrior/portrait/beard/01.png", left=0.25),
        portrait_hair=PortraitPiece(image="img/warrior/portrait/hair/01.png"),
        beard_colour=HairColour(hex="#6b3a1f"),
        hair_colour=HairColour(hex="#2a1a10"),
    )


def test_portrait_stands_a_silhouette_in_for_a_man_with_no_face():
    html = render_component(tag=PORTRAIT_TAG, context={"warrior": WarriorFactory.build(portrait_face=None)})

    result = (parse(html).find("img"), parse(html).find("span")["class"][-2:])

    assert result == (None, ["border", "border-rule"])


def test_portrait_stacks_the_face_beard_and_hair():
    html = render_component(tag=PORTRAIT_TAG, context={"warrior": _drawn_warrior()})

    result = [img["src"].rsplit("/", 2)[-2] for img in parse(html).find_all("img")]

    assert result == ["face", "beard", "hair"]


def test_portrait_tints_a_layer_with_its_colour():
    html = render_component(tag=PORTRAIT_TAG, context={"warrior": _drawn_warrior()})

    result = [layer["style"] for layer in parse(html).select(".portrait-layer")]

    assert "--tint: #6b3a1f;" in result[0]


def test_portrait_crops_to_the_card_unless_asked():
    html = render_component(tag=PORTRAIT_TAG, context={"warrior": _drawn_warrior()})

    result = parse(html).select_one(".portrait")["class"]

    assert "portrait-card" in result


def test_portrait_shows_the_whole_canvas_when_asked():
    html = render_component(
        tag='<c-warrior.portrait :warrior="warrior" crop="full" frame="" />', context={"warrior": _drawn_warrior()}
    )

    result = parse(html).select_one(".portrait")["class"]

    assert "portrait-full" in result
