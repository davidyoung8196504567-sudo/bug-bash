"""Hidden tests: never shown to the model. Used to validate the reference
and to filter out mutants that do not change observable behaviour."""
import datetime as dt

from impl import is_open, minutes_until_open

MON = dt.date(2026, 11, 2)  # a Monday
NO_HOLIDAYS = set()


def at(day, h, m, s=0, us=0):
    return dt.datetime.combine(day, dt.time(h, m, s, us))


def test_open_midday_weekday():
    assert is_open(at(MON, 12, 0), NO_HOLIDAYS)


def test_open_at_exact_opening():
    assert is_open(at(MON, 8, 30), NO_HOLIDAYS)


def test_closed_just_before_opening():
    assert not is_open(at(MON, 8, 29, 59, 999999), NO_HOLIDAYS)


def test_open_just_before_closing():
    assert is_open(at(MON, 16, 29, 59), NO_HOLIDAYS)


def test_closed_at_exact_closing():
    assert not is_open(at(MON, 16, 30), NO_HOLIDAYS)


def test_friday_open_saturday_sunday_closed():
    assert is_open(at(MON + dt.timedelta(days=4), 10, 0), NO_HOLIDAYS)
    assert not is_open(at(MON + dt.timedelta(days=5), 10, 0), NO_HOLIDAYS)
    assert not is_open(at(MON + dt.timedelta(days=6), 10, 0), NO_HOLIDAYS)


def test_holiday_closed():
    assert not is_open(at(MON, 12, 0), {MON})


def test_minutes_zero_when_open():
    assert minutes_until_open(at(MON, 12, 0), NO_HOLIDAYS) == 0


def test_minutes_same_morning():
    assert minutes_until_open(at(MON, 8, 0), NO_HOLIDAYS) == 30


def test_minutes_rounds_up_partial_minute():
    assert minutes_until_open(at(MON, 8, 29, 30), NO_HOLIDAYS) == 1


def test_minutes_after_close_to_next_morning():
    assert minutes_until_open(at(MON, 16, 30), NO_HOLIDAYS) == 16 * 60


def test_minutes_friday_evening_skips_weekend():
    fri = MON + dt.timedelta(days=4)
    assert minutes_until_open(at(fri, 16, 30), NO_HOLIDAYS) == 64 * 60


def test_minutes_thursday_evening_opens_friday():
    thu = MON + dt.timedelta(days=3)
    assert minutes_until_open(at(thu, 16, 30), NO_HOLIDAYS) == 16 * 60


def test_minutes_saturday_noon_opens_monday():
    sat = MON + dt.timedelta(days=5)
    assert minutes_until_open(at(sat, 12, 0), NO_HOLIDAYS) == 44 * 60 + 30


def test_minutes_skips_holiday_monday():
    sat = MON + dt.timedelta(days=5)
    tue = MON + dt.timedelta(days=8)
    expected = (at(tue, 8, 30) - at(sat, 12, 0)).total_seconds() / 60
    assert minutes_until_open(at(sat, 12, 0), {MON + dt.timedelta(days=7)}) == expected


def test_minutes_holiday_morning_goes_to_next_day():
    assert minutes_until_open(at(MON, 8, 0), {MON}) == (24 * 60 + 30)
