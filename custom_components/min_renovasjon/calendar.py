from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .coordinator import MinRenovasjonCoordinator
from datetime import datetime, time
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Min Renovasjon calendar."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MinRenovasjonCalendar(coordinator)], True)

class MinRenovasjonCalendar(CoordinatorEntity, CalendarEntity):
    """Min Renovasjon Calendar."""

    def __init__(self, coordinator: MinRenovasjonCoordinator):
        """Initialize Min Renovasjon Calendar."""
        super().__init__(coordinator)
        self._attr_name = "Min Renovasjon Collection"
        # Safe unique_id generation with fallback
        try:
            entry_id = coordinator.config_entry.entry_id
        except AttributeError:
            entry_id = "min_renovasjon_unknown"
        self._attr_unique_id = f"{entry_id}_calendar"

    @property
    def event(self):
        """Return the next upcoming event."""
        if not self.coordinator.data:
            return None

        # Find the earliest upcoming collection from all fractions
        earliest_event = None
        earliest_date = None

        for fraction_data in self.coordinator.data.values():
            if not fraction_data or len(fraction_data) < 4:
                continue

            fraction_id = fraction_data[0]
            fraction_name = fraction_data[1]
            next_pickup = fraction_data[3]
            next_next_pickup = fraction_data[4] if len(fraction_data) >= 5 else None

            # Check both next and next-next dates
            for pickup_date in [next_pickup, next_next_pickup]:
                if pickup_date is None or not isinstance(pickup_date, datetime):
                    continue

                if earliest_date is None or pickup_date < earliest_date:
                    earliest_date = pickup_date
                    try:
                        start_datetime = datetime.combine(pickup_date.date(), time.min).replace(tzinfo=dt_util.UTC)
                        end_datetime = datetime.combine(pickup_date.date(), time(23, 59)).replace(tzinfo=dt_util.UTC)
                        earliest_event = CalendarEvent(
                            summary=fraction_name,
                            start=start_datetime,
                            end=end_datetime,
                        )
                    except (AttributeError, TypeError, ValueError) as e:
                        _LOGGER.warning(f"Error processing calendar event dates: {e}")
                        continue

        return earliest_event

    async def async_get_events(self, hass, start_date, end_date):
        """Return events within a start and end date."""
        if not self.coordinator.data:
            return []

        events = []
        processed_dates = set()  # Track processed dates to avoid duplicates

        for fraction_data in self.coordinator.data.values():
            if not fraction_data or len(fraction_data) < 5:
                continue

            # Get the collection dates (indices 3 and 4 are next_pickup and next_next_pickup)
            fraction_id = fraction_data[0]
            fraction_name = fraction_data[1]
            next_pickup = fraction_data[3]
            next_next_pickup = fraction_data[4]

            dates = [next_pickup, next_next_pickup]
            for date in dates:
                if date is None:
                    continue

                # Create unique key combining date and fraction to allow multiple collections on same day
                date_key = (date.date(), fraction_id)
                if date_key in processed_dates:
                    continue
                processed_dates.add(date_key)

                # Make dates timezone-aware for comparison and event creation
                date_midnight = datetime.combine(date.date(), time.min).replace(tzinfo=dt_util.UTC)
                date_same_day_end = datetime.combine(date.date(), time(23, 59)).replace(tzinfo=dt_util.UTC)

                if start_date <= date_midnight <= end_date or start_date <= date_same_day_end <= end_date:
                    events.append(
                        CalendarEvent(
                            summary=fraction_name,
                            start=date_midnight,
                            end=date_same_day_end,
                        )
                    )

        return events
