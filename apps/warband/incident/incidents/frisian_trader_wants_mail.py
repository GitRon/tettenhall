import random

from apps.warband.faction.models.faction import Faction
from apps.warband.incident.incidents.base import (
    Incident,
    IncidentOption,
    IncidentOutcome,
    IncidentQuestion,
    losable_items,
)
from apps.warband.incident.models.pending_incident import PendingIncident
from apps.warband.item.models.item_type import ItemType


class FrisianTraderWantsMail(Incident):
    """
    Silver for a piece of armour the war band can spare - the one question that pulls the gear lever.

    Only armour, because the trader wants to wear it, and only what [losable_items] would let a moor
    take: the finest suit in the field is never on offer. The piece is chosen when the question is
    asked and kept on the pending row, so the answer sells the one the question named.
    """

    WEIGHT = 2

    TITLE = "A Frisian trader offered good silver for a spare {item}."
    BODY = "He had already tried it on."

    OPTIONS = (
        IncidentOption(
            key="sell",
            label="Sell it",
            title="The spare {item} went to a Frisian trader.",
            body="He paid in good coin and left wearing it.",
            silver_change=70,
            sells_item=True,
        ),
        IncidentOption(
            key="keep",
            label="Keep it",
            title="The Frisian trader went away without the {item}.",
            body="He said it would not have fitted anyway.",
        ),
    )
    DEFAULT_OPTION = "keep"

    @classmethod
    def is_possible(cls, *, faction: Faction) -> bool:
        return bool(cls._spare_armour(faction=faction))

    @classmethod
    def ask(cls, *, faction: Faction) -> IncidentQuestion:
        item = random.choice(cls._spare_armour(faction=faction))

        return IncidentQuestion(title=cls.TITLE.format(item=item.type.name.lower()), body=cls.BODY, item=item)

    @classmethod
    def answer(cls, *, option: IncidentOption, pending_incident: PendingIncident) -> IncidentOutcome:
        outcome = super().answer(option=option, pending_incident=pending_incident)
        # The piece can be gone by the time the default lands - sold, or lost in the moor - and the
        # line still has to read. Selling it is refused before then, see get_incident_answer_refusal
        item_name = pending_incident.item.type.name.lower() if pending_incident.item else "mail"
        outcome.title = outcome.title.format(item=item_name)

        return outcome

    @classmethod
    def _spare_armour(cls, *, faction: Faction) -> list:
        return [
            item
            for item in losable_items(faction=faction)
            if item.type.function == ItemType.FunctionChoices.FUNCTION_ARMOR
        ]
