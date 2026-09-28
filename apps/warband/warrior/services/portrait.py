import random

from apps.warband.warrior.choices.portrait_kind import PortraitKindChoices
from apps.warband.warrior.models.hair_colour import HairColour
from apps.warband.warrior.models.portrait_piece import PortraitPiece

# The share of men whose beard is not the colour of their hair. Most beards match, and a band where
# every other man wears two colours reads as a costume rather than as men - but a red beard under
# brown hair is common enough in life that never drawing one would make the whole war band a set.
BEARD_COLOUR_DIFFERS_SHARE = 0.2


def draw_portrait() -> dict:
    """
    A man's look, as the five columns "Warrior" stores it under.

    Every piece is equally likely, and bald and clean-shaven each count as one more hairstyle and one
    more beard: a man without either is a look like any other, not a rarity. Colour is drawn per man
    rather than per culture - a Norse war band of seven redheads reads worse than a mixed one.

    Faces are shared by every culture until there are enough to sort, see #362.
    """
    faces = list(PortraitPiece.objects.of_kind(kind=PortraitKindChoices.KIND_FACE))
    colours = list(HairColour.objects.all())
    if not faces or not colours:
        raise RuntimeError(
            "No portrait pieces or hair colours found. "
            "Load the reference data with "
            "'loaddata culture itemtype questtype injurytype traittype portraitpiece haircolour'."
        )

    hairstyles = [*PortraitPiece.objects.of_kind(kind=PortraitKindChoices.KIND_HAIR), None]
    beards = [*PortraitPiece.objects.of_kind(kind=PortraitKindChoices.KIND_BEARD), None]
    hair_colour = random.choice(colours)
    beard_colour = hair_colour
    if random.random() < BEARD_COLOUR_DIFFERS_SHARE:
        # Drawn from the other colours, so a man whose beard is his own colour really has two
        beard_colour = random.choice([colour for colour in colours if colour != hair_colour])

    return {
        "portrait_face": random.choice(faces),
        "portrait_hair": random.choice(hairstyles),
        "portrait_beard": random.choice(beards),
        "hair_colour": hair_colour,
        "beard_colour": beard_colour,
    }
