"""
Timezone utilities for consistent date calculations across the application.

Handles timezone configuration from .env file and provides utilities for
converting timestamps to the configured server timezone.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import re
from ..core.settings import settings


def parse_timezone_offset(tz_string: str) -> timezone:
    """
    Parse timezone string to timezone object.
    
    Supports formats:
    - "UTC-5" or "UTC -5" -> UTC-05:00
    - "UTC+3" or "UTC +3" -> UTC+03:00
    - "America/New_York" -> Uses pytz (if available) or falls back to UTC
    - "UTC" -> UTC (no offset)
    
    Args:
        tz_string: Timezone string from .env
        
    Returns:
        timezone object
    """
    tz_string = tz_string.strip()
    original_tz_string = tz_string  # Keep original for named timezones
    tz_string_upper = tz_string.upper()
    
    # Handle UTC with offset (e.g., "UTC-5", "UTC -5", "UTC+3")
    offset_match = re.match(r'UTC\s*([+-]?)(\d+)', tz_string_upper)
    if offset_match:
        sign = offset_match.group(1) or '-'
        hours = int(offset_match.group(2))
        offset = timedelta(hours=hours if sign == '+' else -hours)
        return timezone(offset)
    
    # Handle UTC (no offset)
    if tz_string_upper == "UTC":
        return timezone.utc
    
    # For named timezones (e.g., "America/New_York"), try to use zoneinfo or pytz
    # Fall back to UTC if not available
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(original_tz_string)
    except ImportError:
        try:
            import pytz
            return pytz.timezone(original_tz_string)
        except (ImportError, pytz.UnknownTimeZoneError):
            # Fall back to UTC if timezone library not available or unknown timezone
            return timezone.utc
    except Exception:
        # Fall back to UTC on any error
        return timezone.utc


def get_timezone_offset_string(tz: timezone) -> str:
    """
    Get PostgreSQL-compatible timezone offset string.
    
    Examples:
    - UTC-05:00 -> "-05:00"
    - UTC+03:00 -> "+03:00"
    - UTC -> "UTC"
    
    Args:
        tz: timezone object
        
    Returns:
        PostgreSQL timezone offset string
    """
    if tz == timezone.utc:
        return "UTC"
    
    # Get UTC offset
    now_utc = datetime.now(timezone.utc)
    offset = tz.utcoffset(now_utc)
    
    if offset is None:
        return "UTC"
    
    # Convert to hours and minutes
    total_seconds = int(offset.total_seconds())
    hours = total_seconds // 3600
    minutes = abs((total_seconds % 3600) // 60)
    
    # Format as PostgreSQL timezone string (e.g., "-05:00", "+03:00")
    sign = "+" if hours >= 0 else "-"
    return f"{sign}{abs(hours):02d}:{minutes:02d}"


def get_server_timezone() -> timezone:
    """
    Get the configured server timezone from settings.
    
    Returns:
        timezone object for the configured server timezone
    """
    return parse_timezone_offset(settings.TIME_ZONE)


def now_in_server_tz() -> datetime:
    """
    Get current datetime in the configured server timezone.
    
    Returns:
        datetime object in server timezone
    """
    server_tz = get_server_timezone()
    return datetime.now(server_tz)


def utc_to_server_tz(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to server timezone.
    
    Args:
        utc_dt: UTC datetime (timezone-aware or naive, assumed UTC)
        
    Returns:
        datetime in server timezone
    """
    server_tz = get_server_timezone()
    
    # If naive, assume UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    # Convert to server timezone
    return utc_dt.astimezone(server_tz)


def get_date_in_server_tz(dt: Optional[datetime] = None) -> datetime.date:
    """
    Get date in server timezone.
    
    Args:
        dt: Optional datetime (defaults to now)
        
    Returns:
        date object in server timezone
    """
    if dt is None:
        dt = now_in_server_tz()
    else:
        # Convert to server timezone if needed
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(get_server_timezone())
    
    return dt.date()


def get_postgresql_timezone_string() -> str:
    """
    Get PostgreSQL-compatible timezone string for use in SQL queries.
    
    Returns:
        PostgreSQL timezone string (e.g., "-05:00", "UTC", "America/New_York")
    """
    server_tz = get_server_timezone()
    
    # For offset-based timezones, return offset string
    if server_tz == timezone.utc:
        return "UTC"
    
    # Check if it's a fixed offset timezone
    try:
        offset_str = get_timezone_offset_string(server_tz)
        return offset_str
    except Exception:
        # For named timezones, return the timezone name
        # This requires the timezone name to be stored somewhere
        # For now, fall back to UTC
        return "UTC"

