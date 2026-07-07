from datetime import datetime, timezone

from app.core.scheduler import _is_due


def test_is_due_matches_delivery_hour_not_quarter_hour_bucket() -> None:
    assert _is_due(
        frequency="daily",
        delivery_day=0,
        utc_delivery_hour=8,
        utc_delivery_minute=45,
        current_utc_hour=8,
        current_utc_minute=0,
        current_dow=1,
        now_utc=datetime(2026, 7, 7, 8, 0, tzinfo=timezone.utc),
    )


def test_is_due_rejects_wrong_hour() -> None:
    assert not _is_due(
        frequency="daily",
        delivery_day=0,
        utc_delivery_hour=8,
        utc_delivery_minute=0,
        current_utc_hour=9,
        current_utc_minute=0,
        current_dow=1,
        now_utc=datetime(2026, 7, 7, 9, 0, tzinfo=timezone.utc),
    )
