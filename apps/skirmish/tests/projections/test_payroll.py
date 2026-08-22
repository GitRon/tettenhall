import pytest

from apps.faction.tests.factories.faction import FactionFactory
from apps.skirmish.projections.payroll import Payroll
from apps.skirmish.tests.factories.warrior import WarriorFactory


def test_paid_warrior_list_holds_the_whole_roster_when_the_purse_covers_it():
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=1, monthly_salary=30), WarriorFactory.build(id=2, monthly_salary=40)],
        budget=100,
        leader_id=1,
    )

    assert [warrior.id for warrior in payroll.paid_warrior_list] == [1, 2]
    assert payroll.unpaid_warrior_list == []


def test_paid_warrior_list_stops_where_the_silver_does():
    """
    The dearest man is the one left short, because the roster arrives cheapest first - so this is
    also the assertion that the projection does not sort it again.
    """
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=1, monthly_salary=30), WarriorFactory.build(id=2, monthly_salary=40)],
        budget=50,
        leader_id=1,
    )

    assert [warrior.id for warrior in payroll.paid_warrior_list] == [1]
    assert [warrior.id for warrior in payroll.unpaid_warrior_list] == [2]


def test_paid_warrior_list_is_empty_on_an_empty_purse():
    payroll = Payroll(warrior_list=[WarriorFactory.build(id=1, monthly_salary=30)], budget=0, leader_id=1)

    assert payroll.paid_warrior_list == []
    assert [warrior.id for warrior in payroll.unpaid_warrior_list] == [1]


def test_amounts_split_the_wage_bill():
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=1, monthly_salary=30), WarriorFactory.build(id=2, monthly_salary=40)],
        budget=50,
        leader_id=1,
    )

    assert (payroll.paid_amount, payroll.missing_amount) == (30, 40)
    assert payroll.total_amount == 70


def test_remaining_amount_is_what_the_purse_keeps():
    payroll = Payroll(warrior_list=[WarriorFactory.build(id=1, monthly_salary=30)], budget=100, leader_id=1)

    assert payroll.remaining_amount == 70


def test_is_short_when_a_warrior_goes_unpaid():
    payroll = Payroll(warrior_list=[WarriorFactory.build(id=1, monthly_salary=30)], budget=0, leader_id=1)

    assert payroll.is_short is True


def test_is_short_stays_false_while_the_wages_are_covered():
    payroll = Payroll(warrior_list=[WarriorFactory.build(id=1, monthly_salary=30)], budget=30, leader_id=1)

    assert payroll.is_short is False


def test_months_until_desertion_names_the_number_the_punishment_reads():
    payroll = Payroll(warrior_list=[], budget=0, leader_id=1)

    assert payroll.months_until_desertion == 3


def test_deserting_warrior_list_names_the_man_on_his_last_month():
    """
    Two months already gone without, so the month being projected is the third - which is what
    handle_punish_unpaid_warrior acts on, since the salary run has recorded the failure by then.
    """
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=2, monthly_salary=30, unpaid_months=2)], budget=0, leader_id=1
    )

    assert [warrior.id for warrior in payroll.deserting_warrior_list] == [2]


def test_deserting_warrior_list_leaves_out_a_warrior_with_months_to_go():
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=2, monthly_salary=30, unpaid_months=1)], budget=0, leader_id=1
    )

    assert payroll.deserting_warrior_list == []


def test_deserting_warrior_list_leaves_out_the_leader():
    """
    He never walks over wages - losing him defeats the faction, so he sulks indefinitely - and a
    warning saying otherwise would promise something the month does not deliver.
    """
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=1, monthly_salary=30, unpaid_months=5)], budget=0, leader_id=1
    )

    assert payroll.deserting_warrior_list == []


def test_deserting_warrior_list_ignores_a_warrior_who_is_getting_paid():
    payroll = Payroll(
        warrior_list=[WarriorFactory.build(id=2, monthly_salary=30, unpaid_months=2)], budget=30, leader_id=1
    )

    assert payroll.deserting_warrior_list == []


@pytest.mark.django_db
def test_for_faction_reads_the_roster_and_the_leader_off_the_faction():
    """
    The one place this projection touches the database, so it is also the only test here needing it.
    """
    faction = FactionFactory()
    leader = WarriorFactory(faction=faction, monthly_salary=40)
    faction.leader = leader
    faction.save()
    WarriorFactory(faction=faction, monthly_salary=30, unpaid_months=2)

    payroll = Payroll.for_faction(faction=faction, budget=30)

    assert (payroll.paid_amount, payroll.missing_amount) == (30, 40)
    assert payroll.deserting_warrior_list == []
