"""Unit tests for LunarDump schedule expression parser."""

import pytest
from datetime import datetime
from lunardump.core.scheduler.parser import ScheduleParser, parse_schedule, parse_time_str


def test_parse_time_str():
    assert parse_time_str("2") == (2, 0)
    assert parse_time_str("14.5") == (14, 5)
    assert parse_time_str("14.30") == (14, 30)
    assert parse_time_str("14:30") == (14, 30)
    assert parse_time_str("0.5") == (0, 5)


def test_daily_schedule():
    parser = parse_schedule("day-2")
    assert parser.cron_expr == "0 2 * * *"
    assert "Daily at 02:00" in parser.description

    parser_half = parse_schedule("day-14.5")
    assert parser_half.cron_expr == "5 14 * * *"
    assert "Daily at 14:05" in parser_half.description


def test_weekly_schedule():
    parser = parse_schedule("week-14.5")
    assert parser.cron_expr == "5 14 * * 0"
    assert "Weekly on Sunday at 14:05" in parser.description

    parser_mon = parse_schedule("week-mon-14.30")
    assert parser_mon.cron_expr == "30 14 * * 1"
    assert "Weekly on Monday at 14:30" in parser_mon.description


def test_monthly_schedule():
    parser = parse_schedule("month-1-2")
    assert parser.cron_expr == "0 2 1 * *"
    assert "Monthly on day 1 at 02:00" in parser.description

    parser_fifteen = parse_schedule("month-15-14.5")
    assert parser_fifteen.cron_expr == "5 14 15 * *"
    assert "Monthly on day 15 at 14:05" in parser_fifteen.description


def test_relative_interval():
    p15m = parse_schedule("every-15m")
    assert p15m.interval_seconds == 900
    assert p15m.cron_expr == "*/15 * * * *"

    p10s = parse_schedule("10s")
    assert p10s.interval_seconds == 10

    p2h = parse_schedule("2h")
    assert p2h.interval_seconds == 7200
    assert p2h.cron_expr == "0 */2 * * *"


def test_standard_cron():
    parser = parse_schedule("0 2 * * *")
    assert parser.cron_expr == "0 2 * * *"

    base = datetime(2026, 8, 3, 1, 0, 0)
    next_run = parser.get_next_run(base)
    assert next_run == datetime(2026, 8, 3, 2, 0, 0)


def test_invalid_schedule():
    with pytest.raises(ValueError):
        parse_schedule("invalid-syntax-xyz")
