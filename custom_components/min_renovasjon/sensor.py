from __future__ import annotations

from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MinRenovasjonCoordinator

import logging

_LOGGER = logging.getLogger(__name__)

class MinRenovasjonNextCollectionSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: MinRenovasjonCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_next_collection"
        self._attr_name = "Min Renovasjon Next Collection"

    @property
    def state(self) -> str:
        try:
            next_collections = {}
            for fraction_id in self.coordinator.fractions:
                fraction_data = self.coordinator.data.get(fraction_id)
                if not fraction_data or len(fraction_data) <= 3 or not fraction_data[3]:
                    continue
                
                collection_date = fraction_data[3]
                if not isinstance(collection_date, datetime):
                    continue
                    
                date_str = collection_date.date().isoformat()
                if date_str not in next_collections:
                    next_collections[date_str] = []
                next_collections[date_str].append(self.coordinator.min_renovasjon.get_fraction_name(fraction_id))

            if not next_collections:
                return "Unavailable"

            # Get the earliest date
            earliest_date = min(next_collections.keys())
            fractions = next_collections[earliest_date]
            return " og ".join(fractions)

        except Exception as e:
            _LOGGER.exception("Error getting state for next collection sensor: %s", e)
            return "Unavailable"

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        attributes = {}
        try:
            next_date = None
            for fraction_id in self.coordinator.fractions:
                fraction_data = self.coordinator.data.get(fraction_id)
                if not fraction_data or len(fraction_data) <= 3 or not fraction_data[3]:
                    continue
                    
                collection_date = fraction_data[3]
                if not isinstance(collection_date, datetime):
                    continue
                    
                if next_date is None or collection_date < next_date:
                    next_date = collection_date

            if next_date:
                days_until = (next_date.date() - datetime.now().date()).days
                attributes["days_until"] = max(0, days_until)
                attributes["next_collection_date"] = next_date.strftime("%d/%m/%Y")

        except Exception as e:
            _LOGGER.error("Error getting extra state attributes for next collection sensor: %s", e)

        return attributes

class MinRenovasjonSensor(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator: MinRenovasjonCoordinator, fraction_id: str) -> None:
        super().__init__(coordinator)
        self._fraction_id = fraction_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{fraction_id}"
        self._attr_name = f"Min Renovasjon {coordinator.min_renovasjon.get_fraction_name(fraction_id)}"
        _LOGGER.debug("Initialized sensor for fraction %s with name %s", fraction_id, self._attr_name)

    @property
    def state(self) -> str:
        _LOGGER.debug("Getting state for fraction %s", self._fraction_id)
        _LOGGER.debug("Coordinator data: %s", self.coordinator.data)
        
        try:
            fraction_data = self.coordinator.data.get(self._fraction_id)
            _LOGGER.debug("Fraction data for %s: %s", self._fraction_id, fraction_data)
            
            if fraction_data and len(fraction_data) > 3 and fraction_data[3]:
                state = self.coordinator.min_renovasjon.format_date(fraction_data[3])
                _LOGGER.debug("Formatted state for fraction %s: %s", self._fraction_id, state)
                return state
            else:
                _LOGGER.warning("Invalid or missing data for fraction %s", self._fraction_id)
        except Exception as e:
            _LOGGER.exception("Error getting state for fraction %s: %s", self._fraction_id, e)
        
        return "Unknown"

    @property
    def entity_picture(self) -> str | None:
        try:
            fraction_data = self.coordinator.data.get(self._fraction_id)
            if fraction_data and len(fraction_data) > 2:
                return fraction_data[2]
        except Exception as e:
            _LOGGER.error("Error getting entity picture for fraction %s: %s", self._fraction_id, e)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attributes = {}
        try:
            fraction_data = self.coordinator.data.get(self._fraction_id)
            if fraction_data:
                if len(fraction_data) > 4 and fraction_data[4]:
                    attributes["next_collection"] = self.coordinator.min_renovasjon.format_date(fraction_data[4])
                if len(fraction_data) > 3 and fraction_data[3]:
                    next_date = fraction_data[3]
                    if isinstance(next_date, datetime):
                        days_until = (next_date.date() - datetime.now().date()).days
                        attributes["days_until"] = max(0, days_until)
                attributes["fraction_name"] = self.coordinator.min_renovasjon.get_fraction_name(self._fraction_id)
            _LOGGER.debug("Extra state attributes for fraction %s: %s", self._fraction_id, attributes)
        except Exception as e:
            _LOGGER.error("Error getting extra state attributes for fraction %s: %s", self._fraction_id, e)
        return attributes

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    if not isinstance(coordinator, MinRenovasjonCoordinator):
        raise TypeError("Coordinator is not of type MinRenovasjonCoordinator")
    
    _LOGGER.debug("Setting up sensors for fractions: %s", coordinator.fractions)
    
    entities = [MinRenovasjonSensor(coordinator, fraction_id) for fraction_id in coordinator.fractions]
    entities.append(MinRenovasjonNextCollectionSensor(coordinator))
    
    async_add_entities(entities)
