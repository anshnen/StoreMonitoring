from app.models import BusinessHours, Store, Timezone
from datetime import datetime, timedelta
import pytz


def compute_uptime(store_id, start_date=None, end_date=None):
    if not start_date:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    store_timezone = get_store_timezone(store_id)
    store_business_hours = get_store_business_hours(store_id)
    hours_open = compute_business_hours_overlap(store_business_hours, store_timezone, start_date, end_date)
    uptime = hours_open / timedelta(hours=24) * 100
    downtime = 100 - uptime

    return uptime, downtime


def get_store_timezone(store_id):
    timezone_entry = Timezone.query.filter_by(store_id=store_id).first()
    if timezone_entry is None:
        return pytz.timezone('UTC')
    return pytz.timezone(timezone_entry.timezone_str)


def get_store_business_hours(store_id):
    business_hours_entries = BusinessHours.query.filter_by(store_id=store_id).all()
    return [(bh.day_of_week, bh.start_time_local, bh.end_time_local) for bh in business_hours_entries]


def compute_business_hours_overlap(store_business_hours, store_timezone, start_date, end_date):
    total_overlap = timedelta()
    for day_of_week, start_time, end_time in store_business_hours:
        start_time_utc = store_timezone.localize(datetime.combine(start_date.date(), start_time)).astimezone(pytz.utc)
        end_time_utc = store_timezone.localize(datetime.combine(end_date.date(), end_time)).astimezone(pytz.utc)
        if start_time_utc >= end_time_utc:
            end_time_utc += timedelta(days=1)
        business_day_start = max(start_date, start_time_utc)
        business_day_end = min(end_date, end_time_utc)
        overlap = (business_day_end - business_day_start).total_seconds() / 3600
        overlap = max(overlap, 0)
        total_overlap += timedelta(hours=overlap)
    return total_overlap

def get_store_uptime_downtime(store_id, start_date, end_date):
    """
    Computes the uptime and downtime for a given store within a given time range.
    """
    store = Store.query.get(store_id)

    # Retrieve the store's timezone
    timezone_str = Timezone.query.filter_by(store_id=store_id).first().timezone_str
    timezone = pytz.timezone(timezone_str)

    # Compute business hours in the local timezone for each day within the given time range
    business_hours = {}
    for day_offset in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=day_offset)
        day_of_week = date.weekday()
        local_start_time = datetime.combine(date, BusinessHours.query.filter_by(store_id=store_id, day_of_week=day_of_week).first().start_time_local)
        local_end_time = datetime.combine(date, BusinessHours.query.filter_by(store_id=store_id, day_of_week=day_of_week).first().end_time_local)
        business_hours[date] = (local_start_time.astimezone(timezone), local_end_time.astimezone(timezone))

    # Retrieve store status changes within the given time range
    status_changes = store.status_changes.filter(Store.timestamp_utc.between(start_date, end_date)).order_by(Store.timestamp_utc).all()

    # Initialize counters for uptime and downtime
    uptime = timedelta()
    downtime = timedelta()

    # Compute uptime and downtime based on status changes and business hours
    last_status = None
    for i, status_change in enumerate(status_changes):
        if i == 0:
            last_status = status_change.status
            continue

        time_diff = status_change.timestamp_utc - status_changes[i - 1].timestamp_utc

        if last_status == "open":
            # Compute downtime during non-business hours
            for j in range((status_changes[i - 1].timestamp_utc.date() - start_date).days, (status_change.timestamp_utc.date() - start_date).days):
                date = start_date + timedelta(days=j)
                if business_hours[date][1] < business_hours[date][0]:
                    downtime += timedelta(hours=24) - (business_hours[date][1] - business_hours[date][0])
                else:
                    downtime += max(timedelta(), business_hours[date][0] - business_hours[date][1])
            uptime += time_diff
        else:
            # Compute uptime during business hours
            for j in range((status_changes[i - 1].timestamp_utc.date() - start_date).days, (status_change.timestamp_utc.date() - start_date).days):
                date = start_date + timedelta(days=j)
                if business_hours[date][1] < business_hours[date][0]:
                    uptime += timedelta(hours=24) - (business_hours[date][1] - business_hours[date][0])
                else:
                    uptime += max(timedelta(), business_hours[date][1] - business_hours[date][0])
            downtime += time_diff

        last_status = status_change.status

    # Compute uptime and downtime for the last status change to the end of the time range
    if last_status == "open":
        for j in range((status_changes[-1].timestamp_utc.date() - start_date).days, (end_date - start_date).days + 1):
            date = start_date + timedelta(days=j)
            if business_hours[date][1] is not None:
                downtime += business_hours[date][1] - business_hours[date][0]

    else:
        for j in range((status_changes[-1].timestamp_utc.date() - start_date).days, (end_date - start_date).days + 1):
            date = start_date + timedelta(days=j)
            if business_hours[date][0] is not None:
                uptime += business_hours[date][1] - business_hours[date][0]

    return uptime, downtime