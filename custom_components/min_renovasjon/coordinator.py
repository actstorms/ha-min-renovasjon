"""DataUpdateCoordinator for Min Renovasjon integration."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    DEFAULT_DATE_FORMAT,
)
from .min_renovasjon import MinRenovasjon

_LOGGER = logging.getLogger(__name__)

class MinRenovasjonCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=24),
        )
        self.min_renovasjon = MinRenovasjon(
            entry.data[CONF_STREET_NAME],
            entry.data[CONF_STREET_CODE],
            entry.data[CONF_HOUSE_NO],
            entry.data[CONF_COUNTY_ID],
            DEFAULT_DATE_FORMAT
        )
        self.fractions = []

    async def _async_update_data(self):
        try:
            _LOGGER.debug("Starting data update in coordinator")
            await self.hass.async_add_executor_job(self.min_renovasjon.refresh_calendar)
            self.fractions = [str(fraction[0]) for fraction in self.min_renovasjon.calender_list]
            _LOGGER.debug("Fractions after refresh: %s", self.fractions)
            
            data = {}
            for fraction_id in self.fractions:
                fraction_data = self.min_renovasjon.get_calender_for_fraction(fraction_id)
                _LOGGER.debug("Fraction data for %s: %s", fraction_id, fraction_data)
                data[fraction_id] = fraction_data
            
            _LOGGER.debug("Final data in coordinator: %s", data)
            return data
        except Exception as err:
            _LOGGER.exception("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err