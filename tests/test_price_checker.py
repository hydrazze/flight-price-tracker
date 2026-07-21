from app.services.price_checker import PriceCheckerService


def checker():
    return PriceCheckerService(
        repository=None,
        client=None,
        notification_service=None,
        price_history_repository=None,
    )


def test_should_notify_first_price_without_target():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=10000,
        target_price=None,
    ) is True


def test_should_notify_price_changed():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=11000,
        target_price=None,
    ) is True


def test_should_not_notify_same_price():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=12000,
        target_price=None,
    ) is False


def test_should_notify_when_target_reached():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=9000,
        target_price=10000,
    ) is True


def test_should_not_notify_when_target_not_reached():
    service = checker()

    assert service.should_notify(
        old_price=12000,
        new_price=11000,
        target_price=10000,
    ) is False


def test_should_notify_first_price_if_target_already_reached():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=9000,
        target_price=10000,
    ) is True


def test_should_not_notify_first_price_if_target_not_reached():
    service = checker()

    assert service.should_notify(
        old_price=None,
        new_price=12000,
        target_price=10000,
    ) is False