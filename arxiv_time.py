from datetime import UTC, datetime, timedelta
from functools import lru_cache

HOLIDAY_2024 = [
    "2024 15 January",
    "2024 22 May",
    "2024 19 June",
    "2024 4 July",
    "2024 2 September",
    "2024 28 November",
    "2024 25 December",
    "2024 26 December",
    "2024 31 December",
]
HOLIDAY_2024_date = [datetime.strptime(d, "%Y %d %B").date() for d in HOLIDAY_2024]


@lru_cache()
def next_arxiv_update_day(time: datetime):
    # see https://info.arxiv.org/help/availability.html
    # arxiv update time is UTC+0 00:00:00

    time.astimezone(UTC)
    time_date = time.replace(hour=0, minute=0, second=0, microsecond=0)
    if time > time_date:
        time = time_date + timedelta(days=1)

    # 上述假期均为美国东部时间（UTC-4），因此9.2放假会导致9.3 UTC+0的更新推迟
    # arxiv的更新时间为周日-周四的美东20:00，对应周一到周五的UTC 00:00
    while time.date() - timedelta(days=1) in HOLIDAY_2024_date or time.weekday() in [5, 6]:
        time = time + timedelta(days=1)
    return time


if __name__ == "__main__":
    print(HOLIDAY_2024_date)
    print(next_arxiv_update_day(datetime.now()))
    print(next_arxiv_update_day(datetime.strptime("2024 9 3", "%Y %m %d")))