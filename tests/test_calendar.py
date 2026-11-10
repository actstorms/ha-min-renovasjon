"""Tests for the Min Renovasjon calendar platform.

Home Assistant is not installed in the test environment, so the imports the
calendar module needs are stubbed before the module is loaded.
"""

import asyncio
import importlib.util
import sys
import types
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "custom_components" / "min_renovasjon"


class CalendarEvent:
    """Minimal stand-in for homeassistant.components.calendar.CalendarEvent."""

    def __init__(self, summary, start, end):
        self.summary = summary
        self.start = start
        self.end = end


class CalendarEntity:
    """Minimal stand-in for the Home Assistant calendar entity base class."""


class CoordinatorEntity:
    """Minimal stand-in for the Home Assistant coordinator entity base class."""

    def __init__(self, coordinator):
        self.coordinator = coordinator


def _add_module(name, path=None, **attrs):
    module = types.ModuleType(name)
    if path is not None:
        module.__path__ = [str(path)]
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


homeassistant = _add_module("homeassistant")
homeassistant_components = _add_module("homeassistant.components")
homeassistant_helpers = _add_module("homeassistant.helpers")
homeassistant_util = _add_module("homeassistant.util")
_add_module(
    "homeassistant.components.calendar",
    CalendarEntity=CalendarEntity,
    CalendarEvent=CalendarEvent,
)
_add_module("homeassistant.helpers.update_coordinator", CoordinatorEntity=CoordinatorEntity)
_add_module(
    "homeassistant.util.dt",
    # Tests run in UTC; only the overlap comparison uses this helper.
    start_of_local_day=lambda value: datetime.combine(
        value.date() if isinstance(value, datetime) else value,
        datetime.min.time(),
        tzinfo=timezone.utc,
    ),
)

custom_components = _add_module("custom_components", path=ROOT / "custom_components")
min_renovasjon = _add_module(
    "custom_components.min_renovasjon", path=PACKAGE_DIR
)
_add_module("custom_components.min_renovasjon.const", DOMAIN="min_renovasjon")
_add_module(
    "custom_components.min_renovasjon.coordinator",
    MinRenovasjonCoordinator=object,
)

spec = importlib.util.spec_from_file_location(
    "custom_components.min_renovasjon.calendar", PACKAGE_DIR / "calendar.py"
)
calendar_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = calendar_module
spec.loader.exec_module(calendar_module)

MinRenovasjonCalendar = calendar_module.MinRenovasjonCalendar


class FakeCoordinator:
    """Coordinator stub that only exposes the data the calendar reads."""

    def __init__(self, data):
        self.data = data
        self.config_entry = types.SimpleNamespace(entry_id="test_entry")


def fraction(fraction_id, name, *pickup_dates):
    return (fraction_id, name, "", *pickup_dates)


def make_calendar(data):
    return MinRenovasjonCalendar(FakeCoordinator(data))


class CalendarEventTests(unittest.TestCase):
    def test_event_is_an_all_day_date_event(self):
        pickup = datetime(2024, 9, 23, 7, 30)
        calendar = make_calendar({"1": fraction(1, "Paper", pickup, None)})

        event = calendar.event

        self.assertEqual(event.summary, "Paper")
        self.assertEqual(event.start, date(2024, 9, 23))
        self.assertEqual(event.end, date(2024, 9, 24))
        self.assertNotIsInstance(event.start, datetime)

    def test_event_returns_earliest_collection_across_fractions(self):
        calendar = make_calendar(
            {
                "1": fraction(1, "Paper", datetime(2024, 10, 7), None),
                "2": fraction(2, "Food", datetime(2024, 9, 23), None),
            }
        )

        event = calendar.event

        self.assertEqual(event.summary, "Food")
        self.assertEqual(event.start, date(2024, 9, 23))

    def test_event_uses_next_next_pickup_when_earlier(self):
        calendar = make_calendar(
            {
                "1": fraction(1, "Paper", datetime(2024, 10, 7), None),
                "2": fraction(
                    2, "Food", datetime(2024, 10, 1), datetime(2024, 9, 23)
                ),
            }
        )

        event = calendar.event

        self.assertEqual(event.summary, "Food")
        self.assertEqual(event.start, date(2024, 9, 23))
        self.assertEqual(event.end, date(2024, 9, 24))

    def test_async_get_events_returns_all_day_date_events(self):
        calendar = make_calendar(
            {
                "1": fraction(
                    1,
                    "Paper",
                    datetime(2024, 9, 23, 7, 30),
                    datetime(2024, 10, 7, 7, 30),
                )
            }
        )

        events = asyncio.run(
            calendar.async_get_events(
                None,
                datetime(2024, 9, 1, tzinfo=timezone.utc),
                datetime(2024, 10, 1, tzinfo=timezone.utc),
            )
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].summary, "Paper")
        self.assertEqual(events[0].start, date(2024, 9, 23))
        self.assertEqual(events[0].end, date(2024, 9, 24))

    def test_async_get_events_range_end_is_exclusive(self):
        calendar = make_calendar(
            {"1": fraction(1, "Paper", datetime(2024, 9, 23), None)}
        )

        overlapping = asyncio.run(
            calendar.async_get_events(
                None,
                datetime(2024, 9, 23, tzinfo=timezone.utc),
                datetime(2024, 9, 24, tzinfo=timezone.utc),
            )
        )
        starting_at_end = asyncio.run(
            calendar.async_get_events(
                None,
                datetime(2024, 9, 1, tzinfo=timezone.utc),
                datetime(2024, 9, 23, tzinfo=timezone.utc),
            )
        )

        self.assertEqual(len(overlapping), 1)
        self.assertEqual(starting_at_end, [])

    def test_async_get_events_outside_range_returns_nothing(self):
        calendar = make_calendar(
            {"1": fraction(1, "Paper", datetime(2024, 9, 23), None)}
        )

        events = asyncio.run(
            calendar.async_get_events(
                None,
                datetime(2024, 10, 1, tzinfo=timezone.utc),
                datetime(2024, 10, 8, tzinfo=timezone.utc),
            )
        )

        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
