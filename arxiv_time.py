from datetime import UTC, datetime, timedelta, date

from zoneinfo import ZoneInfo
from tzlocal import get_localzone

def native_to_arxiv(naive_time:datetime):
    # 获取本地时区
    local_timezone = get_localzone()
    
    # 创建一个本地时间
    local_time = naive_time.replace(tzinfo=local_timezone)
    
    # 获取美国东部时区
    eastern = ZoneInfo("America/New_York")
    
    # 转换为美国东部时间
    arxiv_local_time = local_time.astimezone(eastern)

    return arxiv_local_time


def last_arxiv_update_day(time: datetime, next=False):
    # see https://info.arxiv.org/help/availability.html    
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
    HOLIDAY_2024_date = [datetime.strptime(d, "%Y %d %B") for d in HOLIDAY_2024]

    if next:
        if time.hour >= 20:
            date = time.date() + timedelta(days=1)
        else:
            date = time.date()
    else:
        if time.hour >= 20:
            date = time.date()
        else:
            date = time.date() - timedelta(days=1)
    time = datetime.combine(date, datetime.min.time())

    while time.date() in HOLIDAY_2024_date or time.weekday() in [5, 6]:
        time = time + timedelta(days=1) if next else time - timedelta(days=1)
    return time

def next_arxiv_update_day(time: datetime):
    return last_arxiv_update_day(time, next=True)