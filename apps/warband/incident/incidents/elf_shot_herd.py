from apps.warband.incident.incidents.base import Incident


class ElfShotHerd(Incident):
    """
    The cattle sicken, and superstition sends the bill.

    Dry register: the joke is the charm-woman's accounting, not the herd. The cheapest cost in the
    pool, because the loss it reports is the fee rather than the cattle - a lost herd would want a
    lasting dent in income, which is a duration and does not exist.
    """

    WEIGHT = 3

    TITLE = "The herd sickened, and the leech named it elf-shot."
    BODY = "A charm-woman was paid to sing over the cattle. Those that lived, she said, were the ones she reached."

    SILVER_CHANGE = -60
