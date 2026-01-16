import pytest
from fastapi import HTTPException

from app.throttling import (
    apply_rate_limit,
    user_requests,
    GLOBAL_RATE_LIMIT,
    AUTH_RATE_LIMIT,
)

@pytest.fixture(autouse=True)
def clear_rate_limit_state():
    """
    """
    user_requests.clear()


def test_global_user_rate_limit_exceeded():
    user_id = "global_unauthenticated_user"

    for _ in range(GLOBAL_RATE_LIMIT):
        assert apply_rate_limit(user_id) is True

    with pytest.raises(HTTPException) as exc:
        apply_rate_limit(user_id)

    assert exc.value.status_code == 429
    assert "Too many requests" in exc.value.detail


def test_authenticated_user_rate_limit_exceeded():
    user_id = "user_123"

    for _ in range(AUTH_RATE_LIMIT):
        assert apply_rate_limit(user_id) is True

    with pytest.raises(HTTPException) as exc:
        apply_rate_limit(user_id)

    assert exc.value.status_code == 429

def test_rate_limit_isolated_per_user():
    user_a = "user_a"
    user_b = "user_b"

    for _ in range(AUTH_RATE_LIMIT):
        apply_rate_limit(user_a)

    assert apply_rate_limit(user_b) is True

def test_rate_limit_resets_after_time_window(mocker):
    user_id = "global_unauthenticated_user"
    mocker.patch("app.throttling.time.time", return_value=1000)

    for _ in range(GLOBAL_RATE_LIMIT):
        apply_rate_limit(user_id)

    with pytest.raises(HTTPException):
        apply_rate_limit(user_id)

    mocker.patch("app.throttling.time.time", return_value=2000)
    assert apply_rate_limit(user_id) is True