"""Reference implementation for the business_hours task. See spec.md."""
import datetime
import math

OPEN = datetime.time(8, 30)
CLOSE = datetime.time(16, 30)


def is_open(when, holidays):
    if when.weekday() >= 5:
        return False
    if when.date() in holidays:
        return False
    return OPEN <= when.time() < CLOSE


def _is_business_day(day, holidays):
    return day.weekday() < 5 and day not in holidays


def minutes_until_open(when, holidays):
    if is_open(when, holidays):
        return 0
    day = when.date()
    if _is_business_day(day, holidays) and when.time() < OPEN:
        nxt = datetime.datetime.combine(day, OPEN)
    else:
        day = day + datetime.timedelta(days=1)
        for _ in range(14):
            if _is_business_day(day, holidays):
                break
            day = day + datetime.timedelta(days=1)
        nxt = datetime.datetime.combine(day, OPEN)
    return math.ceil((nxt - when).total_seconds() / 60)
