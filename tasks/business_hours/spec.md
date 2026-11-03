# Task: business_hours

A call centre needs to decide whether a call arriving at a given moment
should be routed to a live agent or to the after-hours message.

## Function

```python
is_open(when: datetime.datetime, holidays: set[datetime.date]) -> bool
```

## Rules

1. The centre is open Monday to Friday only. Saturday and Sunday are closed.
2. Opening time is 08:30. A call at exactly 08:30:00 is answered (open).
3. Closing time is 16:30. A call at exactly 16:30:00 is NOT answered (closed).
   Calls at 16:29:59 are answered.
4. Any date contained in `holidays` is closed all day, even on a weekday.
5. `when` is a naive local datetime. Seconds and microseconds count:
   08:29:59.999999 is closed.

```python
minutes_until_open(when: datetime.datetime, holidays: set[datetime.date]) -> int
```

6. Returns 0 if the centre is open at `when`.
7. Otherwise returns the number of whole minutes until the next opening,
   rounded up (a wait of 30 seconds counts as 1 minute).
8. Holidays and weekends are skipped when looking for the next opening.
   Assume there is always an opening within the next 14 days.
