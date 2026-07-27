from apps.finance.tests.factories.transaction import TransactionFactory


def test_str_contains_reason_and_amount():
    transaction = TransactionFactory.build(reason="Monthly salaries", amount=-250)

    assert str(transaction) == "Monthly salaries (-250 Silver)"
