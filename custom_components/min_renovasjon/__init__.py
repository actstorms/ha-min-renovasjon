from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DATE_FORMAT,
)
from .coordinator import MinRenovasjonCoordinator
from .min_renovasjon import MinRenovasjon

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Min Renovasjon from a config entry."""
    _LOGGER.debug("Setting up Min Renovasjon")
    api = MinRenovasjon(
        entry.data[CONF_STREET_NAME],
        entry.data[CONF_STREET_CODE],
        entry.data[CONF_HOUSE_NO],
        entry.data[CONF_COUNTY_ID],
        DEFAULT_DATE_FORMAT
    )
    await api.get_fraction_types()
    coordinator = MinRenovasjonCoordinator(hass, api, entry.data.get(CONF_UPDATE_INTERVAL, 24))
    coordinator.config_entry = entry  # Add config_entry reference

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
