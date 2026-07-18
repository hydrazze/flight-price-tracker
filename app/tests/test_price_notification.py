from app.services.price_checker import PriceCheckerService


def test_should_notify():

    checker = PriceCheckerService(
        repository=None,
        client=None,
        notification_service=None,
        price_history_repository=None,
    )


    cases = [

        # Есть цель 7000

        (9000, 6500, 7000, True),
        (6500, 6000, 7000, True),
        (6000, 8000, 7000, True),
        (8000, 7000, 7000, True),
        (9000, 10000, 7000, False),


        # Нет цели

        (None, 15000, None, True),
        (15000, 14000, None, True),
        (14000, 14000, None, False),
        (14000, 20000, None, True),
    ]


    for old, new, target, expected in cases:

        result = checker.should_notify(
            old_price=old,
            new_price=new,
            target_price=target,
        )

        assert result == expected
