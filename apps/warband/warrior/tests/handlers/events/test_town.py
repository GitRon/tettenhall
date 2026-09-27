from apps.warband.skirmish.tests.factories.warrior import WarriorFactory
from apps.warband.town.messages.events.town import FeastThrown
from apps.warband.town.tests.factories.town import TownFactory
from apps.warband.warrior.handlers.events.town import handle_feast_mends_cut_ceilings
from apps.warband.warrior.messages.commands.warrior import ChangeWarriorMaxMorale


def _feast(*, warrior_list: list) -> FeastThrown:
    town = TownFactory.build()
    return FeastThrown(
        town=town, faction=town.faction, warrior_list=warrior_list, restored_share=0.2, costs=45, month=5
    )


def test_handle_feast_mends_cut_ceilings_asks_for_a_repair_for_a_man_carrying_a_cut():
    cut = WarriorFactory.build(max_morale=15, peak_max_morale=20)
    context = _feast(warrior_list=[cut])

    result = handle_feast_mends_cut_ceilings(context=context)

    assert result == [
        ChangeWarriorMaxMorale(warrior=cut, faction=context.faction, share=0.2, month=5, restores_toward_peak=True)
    ]


def test_handle_feast_mends_cut_ceilings_passes_over_a_whole_man_and_an_unpaid_one():
    """
    Both are fed and both are charged for, and neither is lifted: the whole man has nothing to mend,
    and the unpaid one would buy back what going broke is meant to cost.
    """
    whole = WarriorFactory.build(max_morale=20, peak_max_morale=20)
    unpaid = WarriorFactory.build(max_morale=15, peak_max_morale=20, unpaid_months=1)

    result = handle_feast_mends_cut_ceilings(context=_feast(warrior_list=[whole, unpaid]))

    assert result == []
