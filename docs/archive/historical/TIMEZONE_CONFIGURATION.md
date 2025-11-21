# Timezone Configuration Guide

## Overview

The Q2O Licensing Platform now supports configurable server timezone for all date calculations across both the **Licensing Admin Dashboard** and **Tenant Dashboard**.

## Configuration

### Setting Timezone in `.env` File

Add the following line to your `.env` file:

```env
TIME_ZONE="UTC-5"
```

### Supported Formats

The `TIME_ZONE` setting supports multiple formats:

1. **UTC Offset Format** (Recommended):
   - `TIME_ZONE="UTC-5"` - UTC minus 5 hours (e.g., EST)
   - `TIME_ZONE="UTC+3"` - UTC plus 3 hours
   - `TIME_ZONE="UTC -5"` - Spaces are allowed

2. **Named Timezones** (if `zoneinfo` or `pytz` available):
   - `TIME_ZONE="America/New_York"`
   - `TIME_ZONE="Europe/London"`
   - `TIME_ZONE="Asia/Tokyo"`

3. **UTC** (Default):
   - `TIME_ZONE="UTC"` - No offset

### Default Value

If `TIME_ZONE` is not set in `.env`, the system defaults to `UTC`.

## Where Timezone is Applied

### Admin Dashboard Endpoints

1. **`/admin/api/dashboard-stats`**
   - Code expiration checks
   - Week-over-week trend calculations
   - All date comparisons

2. **`/admin/api/activation-trend`**
   - Daily code generation counts
   - Project activation dates
   - Device enrollment dates

3. **`/admin/api/analytics`**
   - Date range calculations (today, 7d, 30d, 90d, 1y)
   - Activation trend charts
   - All date-based filtering

4. **`/admin/api/recent-activities`**
   - Event log date filtering
   - Activity timeline calculations

### Tenant Dashboard Endpoints

1. **`/usage/{tenant_slug}`**
   - Current month calculation
   - Usage rollup date matching
   - Monthly quota tracking

## Technical Implementation

### Timezone Utilities (`addon_portal/api/utils/timezone_utils.py`)

The system provides utility functions for consistent timezone handling:

- `get_server_timezone()` - Returns configured timezone object
- `now_in_server_tz()` - Current datetime in server timezone
- `utc_to_server_tz(dt)` - Converts UTC datetime to server timezone
- `get_date_in_server_tz(dt)` - Extracts date in server timezone
- `get_postgresql_timezone_string()` - PostgreSQL-compatible timezone string

### Database Queries

For PostgreSQL queries, timestamps stored as `TIMESTAMP WITHOUT TIME ZONE` (timezone-naive) are interpreted as UTC and then converted to the server timezone:

```sql
DATE((column_name AT TIME ZONE 'UTC') AT TIME ZONE '-05:00')
```

This ensures accurate date extraction regardless of server location.

## Example: Setting EST Timezone

To configure the server for Eastern Standard Time (UTC-5):

1. **Add to `.env` file:**
   ```env
   TIME_ZONE="UTC-5"
   ```

2. **Restart the backend API service**

3. **Verify:**
   - All dashboard dates will now reflect EST
   - Code generation dates will be counted in EST
   - Analytics charts will use EST for date ranges

## Important Notes

- **Database Storage**: All timestamps are still stored in UTC in the database
- **Timezone Conversion**: Conversion happens at query time for display/calculation purposes
- **Consistency**: All endpoints use the same configured timezone for consistency
- **No Data Migration**: Changing timezone does not require database migration - it only affects how dates are calculated and displayed

## Troubleshooting

### Codes Not Showing Up in Today's Count

If codes created today are not appearing in today's count:

1. Check that `TIME_ZONE` is set correctly in `.env`
2. Restart the backend API service
3. Verify the timezone offset matches your server's location

### Date Mismatches

If dates appear incorrect:

1. Verify `TIME_ZONE` format is correct (e.g., `"UTC-5"` not `"UTC -5"` with extra spaces)
2. Check that the backend was restarted after changing `.env`
3. Ensure PostgreSQL timezone functions are working correctly

## Future Enhancements

- Per-tenant timezone configuration
- Automatic timezone detection
- Daylight saving time handling for named timezones

