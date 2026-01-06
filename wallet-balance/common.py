import pytz
from datetime import datetime


def get_boolean_from_value(val: str):
    if not val:
        return False
    
    return val.strip().lower() in ['true', 't', '1', 'yes', 'y']


def get_datetime_now_pt():
    pacific_tz = pytz.timezone("US/Pacific")

    return datetime.now(pacific_tz)

def get_datetime_str_now_pt():
    current_pt_date = get_datetime_now_pt()
    return current_pt_date.strftime("%Y-%m-%d_%H:%M:%S")

# Arbitrary date cutoff date. I don't want to query too far in the past
def is_date_older_than_cutoff(date_str: str, cutoff_str: str = "2025-12-01") -> bool:
    """
    Checks if date_str (in YYYY-MM-DD format) is older than or equal to the cutoff date.
    Returns True if date <= cutoff, False otherwise (or if invalid).
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        cutoff = datetime.strptime(cutoff_str, "%Y-%m-%d").date()
        return date <= cutoff
    except ValueError:
        return False  # Invalid date format