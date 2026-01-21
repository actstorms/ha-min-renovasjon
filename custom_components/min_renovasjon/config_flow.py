from __future__ import annotations

from typing import Any
import voluptuous as vol
import aiohttp
import re

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_STREET_NAME,
    CONF_STREET_CODE,
    CONF_HOUSE_NO,
    CONF_COUNTY_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .min_renovasjon import MinRenovasjon

import logging

_LOGGER = logging.getLogger(__name__)

GEONORGE_API_URL = "https://ws.geonorge.no/adresser/v1/sok"

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("address"): str,
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._address = None
        self._address_search_results = None
        self._selected_address = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - user enters address."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        self._address = user_input["address"]

        # Search for address using Geonorge API
        try:
            self._address_search_results = await self._search_address(self._address)
        except Exception as err:
            _LOGGER.error("Address search failed: %s", err)
            errors["base"] = "search_failed"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        if not self._address_search_results:
            errors["base"] = "no_results"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        # If only one result, skip selection step
        if len(self._address_search_results) == 1:
            self._selected_address = self._address_search_results[0]
            return await self.async_step_confirm()

        # Multiple results - show selection
        return await self.async_step_select_address()

    async def _search_address(self, address: str) -> list[dict[str, Any]]:
        """Search for address using Geonorge API.

        Args:
            address: The address to search for (e.g., "Seljeveien 50 3158 Andebu")

        Returns:
            List of matching addresses with their details
        """
        url = f"{GEONORGE_API_URL}?sok={address}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

                addresses = data.get("adresser", [])

                # Map Geonorge fields to our format
                results = []
                for addr in addresses:
                    results.append({
                        "street_name": addr.get("adressenavn", ""),
                        "house_number": str(addr.get("nummer", "")),
                        "postal_code": addr.get("postnummer", ""),
                        "city": addr.get("poststed", ""),
                        "municipality_id": addr.get("kommunenummer", ""),
                        "municipality_name": addr.get("kommunenavn", ""),
                        "address_code": addr.get("adressekode", ""),
                        "full_address": addr.get("adressetekst", ""),
                    })

                return results

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address selection step when multiple matches found."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_index = int(user_input["address"])
            self._selected_address = self._address_search_results[selected_index]
            return await self.async_step_confirm()

        # Create selection options
        addresses_dict = {}
        for i, addr in enumerate(self._address_search_results):
            label = (
                f"{addr['full_address']}, {addr['postal_code']} {addr['city']}"
                if addr.get('postal_code') and addr.get('city')
                else addr['full_address']
            )
            addresses_dict[str(i)] = label

        data_schema = vol.Schema({
            vol.Required("address"): vol.In(addresses_dict),
        })

        return self.async_show_form(
            step_id="select_address",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle confirmation step - verify address and create entry."""
        errors: dict[str, str] = {}

        if user_input is None:
            # First time showing confirmation form
            return self.async_show_form(
                step_id="confirm",
                data_schema=self._get_confirmation_schema(),
                description_placeholders={
                    "street_name": self._selected_address.get("street_name", ""),
                    "house_number": self._selected_address.get("house_number", ""),
                    "postal_code": self._selected_address.get("postal_code", ""),
                    "city": self._selected_address.get("city", ""),
                    "municipality": self._selected_address.get("municipality_name", ""),
                },
            )

        # User confirmed - create the config entry
        config_data = {
            CONF_STREET_NAME: self._selected_address.get("street_name", ""),
            CONF_STREET_CODE: str(self._selected_address.get("address_code", "")),
            CONF_HOUSE_NO: str(self._selected_address.get("house_number", "")),
            CONF_COUNTY_ID: str(self._selected_address.get("municipality_id", "")),
            CONF_UPDATE_INTERVAL: user_input.get(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL
            ),
        }

        # Validate the configuration by trying to fetch data
        try:
            api = MinRenovasjon(
                config_data[CONF_STREET_NAME],
                config_data[CONF_STREET_CODE],
                config_data[CONF_HOUSE_NO],
                config_data[CONF_COUNTY_ID],
                "%d/%m/%Y"
            )
            await api.get_fraction_types()
            await api.refresh_calendar()
        except Exception as err:
            _LOGGER.error("Validation failed: %s", err)
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="confirm",
                data_schema=self._get_confirmation_schema(),
                errors=errors,
                description_placeholders={
                    "street_name": self._selected_address.get("street_name", ""),
                    "house_number": self._selected_address.get("house_number", ""),
                    "postal_code": self._selected_address.get("postal_code", ""),
                    "city": self._selected_address.get("city", ""),
                    "municipality": self._selected_address.get("municipality_name", ""),
                },
            )

        return self.async_create_entry(
            title=(
                f"Min Renovasjon - {self._selected_address.get('street_name', '')} "
                f"{self._selected_address.get('house_number', '')}, "
                f"{self._selected_address.get('city', '')}"
            ),
            data=config_data
        )

    def _get_confirmation_schema(self):
        """Create the confirmation form schema."""
        return vol.Schema({
            vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int),
                vol.Range(min=1, max=168)
            ),
        })


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
