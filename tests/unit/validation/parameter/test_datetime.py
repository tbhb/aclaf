"""Unit tests for datetime parameter validators."""

from datetime import UTC, date, datetime, timedelta

from aclaf.validation.parameter._datetime import (
    AfterDate,
    AfterDatetime,
    BeforeDate,
    BeforeDatetime,
    DateRange,
    DatetimeRange,
    MaxTimedelta,
    MinTimedelta,
    TimedeltaRange,
    validate_after_date,
    validate_after_datetime,
    validate_before_date,
    validate_before_datetime,
    validate_date_range,
    validate_datetime_range,
    validate_max_timedelta,
    validate_min_timedelta,
    validate_timedelta_range,
)


class TestAfterDate:
    def test_validates_date_after_threshold(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = date(2024, 1, 2)

        result = validate_after_date(value, metadata)

        assert result is None

    def test_rejects_date_equal_to_threshold(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = date(2024, 1, 1)

        result = validate_after_date(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be after 2024-01-01" in result[0]

    def test_rejects_date_before_threshold(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = date(2023, 12, 31)

        result = validate_after_date(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be after 2024-01-01" in result[0]

    def test_validates_datetime_after_threshold(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = datetime(2024, 1, 2, 10, 30, tzinfo=UTC)

        result = validate_after_date(value, metadata)

        assert result is None

    def test_rejects_datetime_on_same_date(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = datetime(2024, 1, 1, 23, 59, tzinfo=UTC)

        result = validate_after_date(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = None

        result = validate_after_date(value, metadata)

        assert result is None

    def test_rejects_non_date_value(self):
        metadata = AfterDate(after=date(2024, 1, 1))
        value = "2024-01-02"

        result = validate_after_date(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a date or datetime" in result[0]


class TestBeforeDate:
    def test_validates_date_before_threshold(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = date(2024, 12, 30)

        result = validate_before_date(value, metadata)

        assert result is None

    def test_rejects_date_equal_to_threshold(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = date(2024, 12, 31)

        result = validate_before_date(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be before 2024-12-31" in result[0]

    def test_rejects_date_after_threshold(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = date(2025, 1, 1)

        result = validate_before_date(value, metadata)

        assert result is not None

    def test_validates_datetime_before_threshold(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = datetime(2024, 12, 30, 10, 30, tzinfo=UTC)

        result = validate_before_date(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = None

        result = validate_before_date(value, metadata)

        assert result is None

    def test_rejects_non_date_value(self):
        metadata = BeforeDate(before=date(2024, 12, 31))
        value = "2024-12-30"

        result = validate_before_date(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a date or datetime" in result[0]


class TestDateRange:
    def test_validates_date_within_exclusive_range(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = date(2024, 6, 15)

        result = validate_date_range(value, metadata)

        assert result is None

    def test_validates_date_within_inclusive_range(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=True,
            inclusive_before=True,
        )
        value = date(2024, 1, 1)

        result = validate_date_range(value, metadata)

        assert result is None

    def test_validates_date_at_inclusive_upper_bound(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=True,
            inclusive_before=True,
        )
        value = date(2024, 12, 31)

        result = validate_date_range(value, metadata)

        assert result is None

    def test_rejects_date_at_exclusive_lower_bound(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = date(2024, 1, 1)

        result = validate_date_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be after 2024-01-01" in result[0]

    def test_rejects_date_at_exclusive_upper_bound(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = date(2024, 12, 31)

        result = validate_date_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be before 2024-12-31" in result[0]

    def test_validates_only_lower_bound(self):
        metadata = DateRange(after=date(2024, 1, 1), inclusive_after=True)
        value = date(2025, 1, 1)

        result = validate_date_range(value, metadata)

        assert result is None

    def test_validates_only_upper_bound(self):
        metadata = DateRange(before=date(2024, 12, 31), inclusive_before=True)
        value = date(2024, 1, 1)

        result = validate_date_range(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = DateRange(after=date(2024, 1, 1), before=date(2024, 12, 31))
        value = None

        result = validate_date_range(value, metadata)

        assert result is None

    def test_rejects_non_date_value(self):
        metadata = DateRange(after=date(2024, 1, 1), before=date(2024, 12, 31))
        value = "2024-06-15"

        result = validate_date_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a date or datetime" in result[0]

    def test_validates_datetime_in_range(self):
        metadata = DateRange(
            after=date(2024, 1, 1),
            before=date(2024, 12, 31),
            inclusive_after=True,
            inclusive_before=True,
        )
        value = datetime(2024, 6, 15, 12, 30, tzinfo=UTC)

        result = validate_date_range(value, metadata)

        assert result is None


class TestAfterDatetime:
    def test_validates_datetime_after_threshold(self):
        metadata = AfterDatetime(after=datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        value = datetime(2024, 1, 1, 12, 1, tzinfo=UTC)

        result = validate_after_datetime(value, metadata)

        assert result is None

    def test_rejects_datetime_equal_to_threshold(self):
        metadata = AfterDatetime(after=datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        value = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)

        result = validate_after_datetime(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be after" in result[0]

    def test_rejects_datetime_before_threshold(self):
        metadata = AfterDatetime(after=datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        value = datetime(2024, 1, 1, 11, 59, tzinfo=UTC)

        result = validate_after_datetime(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = AfterDatetime(after=datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        value = None

        result = validate_after_datetime(value, metadata)

        assert result is None

    def test_rejects_non_datetime_value(self):
        metadata = AfterDatetime(after=datetime(2024, 1, 1, 12, 0, tzinfo=UTC))
        value = "2024-01-01T12:01:00"

        result = validate_after_datetime(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a datetime" in result[0]


class TestBeforeDatetime:
    def test_validates_datetime_before_threshold(self):
        metadata = BeforeDatetime(before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC))
        value = datetime(2024, 12, 31, 23, 58, tzinfo=UTC)

        result = validate_before_datetime(value, metadata)

        assert result is None

    def test_rejects_datetime_equal_to_threshold(self):
        metadata = BeforeDatetime(before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC))
        value = datetime(2024, 12, 31, 23, 59, tzinfo=UTC)

        result = validate_before_datetime(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be before" in result[0]

    def test_rejects_datetime_after_threshold(self):
        metadata = BeforeDatetime(before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC))
        value = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)

        result = validate_before_datetime(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = BeforeDatetime(before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC))
        value = None

        result = validate_before_datetime(value, metadata)

        assert result is None

    def test_rejects_non_datetime_value(self):
        metadata = BeforeDatetime(before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC))
        value = "2024-12-31T23:58:00"

        result = validate_before_datetime(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a datetime" in result[0]


class TestDatetimeRange:
    def test_validates_datetime_within_exclusive_range(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = datetime(2024, 6, 15, 12, 0, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_validates_datetime_within_inclusive_range(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
            inclusive_after=True,
            inclusive_before=True,
        )
        value = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_validates_datetime_at_inclusive_upper_bound(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
            inclusive_after=True,
            inclusive_before=True,
        )
        value = datetime(2024, 12, 31, 23, 59, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_rejects_datetime_at_exclusive_lower_bound(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be after" in result[0]

    def test_rejects_datetime_at_exclusive_upper_bound(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
            inclusive_after=False,
            inclusive_before=False,
        )
        value = datetime(2024, 12, 31, 23, 59, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be before" in result[0]

    def test_validates_only_lower_bound(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC), inclusive_after=True
        )
        value = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_validates_only_upper_bound(self):
        metadata = DatetimeRange(
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC), inclusive_before=True
        )
        value = datetime(2024, 1, 1, 0, 0, tzinfo=UTC)

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
        )
        value = None

        result = validate_datetime_range(value, metadata)

        assert result is None

    def test_rejects_non_datetime_value(self):
        metadata = DatetimeRange(
            after=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            before=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
        )
        value = "2024-06-15T12:00:00"

        result = validate_datetime_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a datetime" in result[0]


class TestMinTimedelta:
    def test_validates_timedelta_above_minimum(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=1))
        value = timedelta(hours=2)

        result = validate_min_timedelta(value, metadata)

        assert result is None

    def test_validates_timedelta_equal_to_minimum(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=1))
        value = timedelta(hours=1)

        result = validate_min_timedelta(value, metadata)

        assert result is None

    def test_rejects_timedelta_below_minimum(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=1))
        value = timedelta(minutes=30)

        result = validate_min_timedelta(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be at least" in result[0]

    def test_validates_none_value(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=1))
        value = None

        result = validate_min_timedelta(value, metadata)

        assert result is None

    def test_rejects_non_timedelta_value(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=1))
        value = "1 hour"

        result = validate_min_timedelta(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a timedelta" in result[0]

    def test_validates_negative_timedelta(self):
        metadata = MinTimedelta(min_duration=timedelta(hours=-2))
        value = timedelta(hours=-1)

        result = validate_min_timedelta(value, metadata)

        assert result is None


class TestMaxTimedelta:
    def test_validates_timedelta_below_maximum(self):
        metadata = MaxTimedelta(max_duration=timedelta(hours=2))
        value = timedelta(hours=1)

        result = validate_max_timedelta(value, metadata)

        assert result is None

    def test_validates_timedelta_equal_to_maximum(self):
        metadata = MaxTimedelta(max_duration=timedelta(hours=2))
        value = timedelta(hours=2)

        result = validate_max_timedelta(value, metadata)

        assert result is None

    def test_rejects_timedelta_above_maximum(self):
        metadata = MaxTimedelta(max_duration=timedelta(hours=2))
        value = timedelta(hours=3)

        result = validate_max_timedelta(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be at most" in result[0]

    def test_validates_none_value(self):
        metadata = MaxTimedelta(max_duration=timedelta(hours=2))
        value = None

        result = validate_max_timedelta(value, metadata)

        assert result is None

    def test_rejects_non_timedelta_value(self):
        metadata = MaxTimedelta(max_duration=timedelta(hours=2))
        value = "2 hours"

        result = validate_max_timedelta(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a timedelta" in result[0]


class TestTimedeltaRange:
    def test_validates_timedelta_within_range(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = timedelta(hours=3)

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_validates_timedelta_at_minimum(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = timedelta(hours=1)

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_validates_timedelta_at_maximum(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = timedelta(hours=5)

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_rejects_timedelta_below_minimum(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = timedelta(minutes=30)

        result = validate_timedelta_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be at least" in result[0]

    def test_rejects_timedelta_above_maximum(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = timedelta(hours=6)

        result = validate_timedelta_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be at most" in result[0]

    def test_validates_only_minimum(self):
        metadata = TimedeltaRange(min_duration=timedelta(hours=1))
        value = timedelta(hours=10)

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_validates_only_maximum(self):
        metadata = TimedeltaRange(max_duration=timedelta(hours=5))
        value = timedelta(minutes=30)

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = None

        result = validate_timedelta_range(value, metadata)

        assert result is None

    def test_rejects_non_timedelta_value(self):
        metadata = TimedeltaRange(
            min_duration=timedelta(hours=1), max_duration=timedelta(hours=5)
        )
        value = "3 hours"

        result = validate_timedelta_range(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a timedelta" in result[0]
