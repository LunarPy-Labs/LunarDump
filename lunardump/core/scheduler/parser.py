"""Schedule expression parser supporting human-friendly strings and standard cron syntax."""

import re
from datetime import datetime, timedelta
from typing import Tuple, Optional
from croniter import croniter


def parse_time_str(time_str: str) -> Tuple[int, int]:
    """Parse time string like '2', '14.5', '14:30', '14.05' into (hour, minute).

    Examples:
        - "2" -> (2, 0)
        - "14.5" -> (14, 5) (i.e. 14:05)
        - "14.30" -> (14, 30) (i.e. 14:30)
        - "14:30" -> (14, 30)
        - "0.5" -> (0, 5) (i.e. 00:05)
    """
    time_str = time_str.strip()

    if ":" in time_str or "." in time_str:
        delimiter = ":" if ":" in time_str else "."
        parts = time_str.split(delimiter)
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return hour, minute

    hour = int(time_str)
    return hour, 0


class ScheduleParser:
    """Parses human-friendly schedule strings and standard cron expressions."""

    def __init__(self, expression: str):
        self.raw_expression = expression.strip()
        self.cron_expr: Optional[str] = None
        self.interval_seconds: Optional[int] = None
        self.description: str = ""
        self._parse()

    def _parse(self):
        expr = self.raw_expression.lower()

        # 1. Short interval syntax: e.g. "10s", "15m", "2h", "1d", "every-10s", "every-15m"
        interval_match = re.match(r"^(?:every-)?(\d+)([smhd])$", expr)
        if interval_match:
            amount = int(interval_match.group(1))
            unit = interval_match.group(2)
            if unit == "s":
                self.interval_seconds = amount
                self.description = f"Every {amount} second(s)"
            elif unit == "m":
                self.interval_seconds = amount * 60
                self.cron_expr = f"*/{amount} * * * *"
                self.description = f"Every {amount} minute(s)"
            elif unit == "h":
                self.interval_seconds = amount * 3600
                self.cron_expr = f"0 */{amount} * * *"
                self.description = f"Every {amount} hour(s)"
            elif unit == "d":
                self.interval_seconds = amount * 86400
                self.cron_expr = f"0 0 */{amount} * *"
                self.description = f"Every {amount} day(s)"
            return

        # 2. Daily format: e.g. "day-2", "day-14.5", "day-14:30"
        daily_match = re.match(r"^day-(.+)$", expr)
        if daily_match:
            hour, minute = parse_time_str(daily_match.group(1))
            self.cron_expr = f"{minute} {hour} * * *"
            self.description = f"Daily at {hour:02d}:{minute:02d}"
            return

        # 3. Weekly format: e.g. "week-14.5", "week-sun-14.5", "week-1-14.5"
        weekly_match = re.match(r"^week-(?:([a-z0-9]+)-)?(.+)$", expr)
        if weekly_match:
            day_part = weekly_match.group(1)
            time_part = weekly_match.group(2)

            day_of_week = "0"  # Default Sunday
            day_name = "Sunday"

            if day_part:
                day_map = {
                    "sun": ("0", "Sunday"), "0": ("0", "Sunday"),
                    "mon": ("1", "Monday"), "1": ("1", "Monday"),
                    "tue": ("2", "Tuesday"), "2": ("2", "Tuesday"),
                    "wed": ("3", "Wednesday"), "3": ("3", "Wednesday"),
                    "thu": ("4", "Thursday"), "4": ("4", "Thursday"),
                    "fri": ("5", "Friday"), "5": ("5", "Friday"),
                    "sat": ("6", "Saturday"), "6": ("6", "Saturday"),
                }
                if day_part in day_map:
                    day_of_week, day_name = day_map[day_part]

            hour, minute = parse_time_str(time_part)
            self.cron_expr = f"{minute} {hour} * * {day_of_week}"
            self.description = f"Weekly on {day_name} at {hour:02d}:{minute:02d}"
            return

        # 4. Monthly format: e.g. "month-1-2", "month-15-14.5", "month-15-14:30"
        monthly_match = re.match(r"^month-(\d+)-(.+)$", expr)
        if monthly_match:
            day_of_month = int(monthly_match.group(1))
            time_part = monthly_match.group(2)
            hour, minute = parse_time_str(time_part)
            self.cron_expr = f"{minute} {hour} {day_of_month} * *"
            self.description = f"Monthly on day {day_of_month} at {hour:02d}:{minute:02d}"
            return

        # 5. Fallback to standard 5-field cron expression
        if croniter.is_valid(self.raw_expression):
            self.cron_expr = self.raw_expression
            self.description = f"Cron: {self.raw_expression}"
            return

        raise ValueError(
            f"Invalid schedule expression '{self.raw_expression}'. "
            "Supported formats: 'day-2', 'day-14.5', 'week-14.5', 'month-1-2', 'month-15-14.5', 'every-15m', or '0 2 * * *'."
        )

    def get_next_run(self, base_time: Optional[datetime] = None) -> datetime:
        """Calculate the next execution datetime from base_time (default now)."""
        now = base_time or datetime.now()

        if self.interval_seconds:
            return now + timedelta(seconds=self.interval_seconds)

        if self.cron_expr:
            iter_cron = croniter(self.cron_expr, now)
            return iter_cron.get_next(datetime)

        raise ValueError("No valid schedule configured")


def parse_schedule(expression: str) -> ScheduleParser:
    """Helper factory function to parse a schedule expression."""
    return ScheduleParser(expression)
