from app.calc import add, is_even


def test_add():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, 1) == 0


def test_is_even():
    assert is_even(4) is True
    assert is_even(3) is False
