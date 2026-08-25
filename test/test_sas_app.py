import pytest

from api.apps.sas_app import calculate_sas_score, get_sas_result


def test_five_item_score_reverses_positive_question():
    assert calculate_sas_score((1, 1, 1, 1, 4)) == 5
    assert calculate_sas_score((4, 4, 4, 4, 1)) == 20


@pytest.mark.parametrize(
    "score, expected",
    [
        (8, "最近的紧张与不安感较少"),
        (9, "最近有一些紧张或不安"),
        (13, "最近较频繁地感到紧张或不安"),
        (17, "最近的紧张或不安感比较强烈"),
    ],
)
def test_self_check_feedback(score, expected):
    assert get_sas_result(score) == expected


def test_score_rejects_invalid_answers():
    with pytest.raises(ValueError):
        calculate_sas_score((1, 2, 3))
