from services.api.src.fixture import fixture_value


def test_fixture_value_is_stable() -> None:
    assert fixture_value() == "fixture"
