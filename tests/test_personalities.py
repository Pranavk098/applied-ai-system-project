import random
from personalities import get_personality, list_personalities, PERSONALITIES


def test_all_four_personalities_exist():
    for key in ["Strategist", "Gambler", "Professor", "TrashTalker"]:
        p = get_personality(key)
        assert p.key == key
        assert p.name
        assert callable(p.strategy)
        assert len(p.fallback_lines) >= 3
        assert p.color.startswith("#")


def test_strategist_always_picks_midpoint():
    p = get_personality("Strategist")
    assert p.strategy(1, 100, []) == 50
    assert p.strategy(1, 101, []) == 51
    assert p.strategy(50, 100, []) == 75
    assert p.strategy(5, 5, []) == 5


def test_all_strategies_return_in_range():
    random.seed(42)
    for key in list_personalities():
        p = get_personality(key)
        for _ in range(50):
            low = random.randint(1, 90)
            high = random.randint(low, 100)
            result = p.strategy(low, high, [])
            assert low <= result <= high, (
                f"{key} returned {result} outside [{low}, {high}]"
            )


def test_list_personalities_returns_all_keys():
    keys = list_personalities()
    assert set(keys) == {"Strategist", "Gambler", "Professor", "TrashTalker"}
