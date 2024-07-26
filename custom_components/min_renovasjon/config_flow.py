from __future__ import annotations

from typing import Any
import voluptuous as vol

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
)

import logging

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        
        if user_input is None:
            data_schema = vol.Schema({
                vol.Required(CONF_STREET_NAME): str,
                vol.Required(CONF_STREET_CODE): str,
                vol.Required(CONF_HOUSE_NO): str,
                vol.Required(CONF_COUNTY_ID): str,
            })
            return self.async_show_form(step_id="user", data_schema=data_schema)

        try:
            return self.async_create_entry(title="Min Renovasjon", data=user_input)
        except Exception: 
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        data_schema = vol.Schema({
            vol.Required(CONF_STREET_NAME, default=user_input.get(CONF_STREET_NAME, "")): str,
            vol.Required(CONF_STREET_CODE, default=user_input.get(CONF_STREET_CODE, "")): str,
            vol.Required(CONF_HOUSE_NO, default=user_input.get(CONF_HOUSE_NO, "")): str,
            vol.Required(CONF_COUNTY_ID, default=user_input.get(CONF_COUNTY_ID, "")): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""