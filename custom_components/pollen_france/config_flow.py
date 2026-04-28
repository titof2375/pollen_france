"""Config flow pour Pollen France."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PollenFranceApi, PollenFranceApiError
from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)


def _schema(hass: HomeAssistant, defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Optional(
                CONF_LATITUDE,
                default=defaults.get(CONF_LATITUDE, hass.config.latitude),
            ): vol.Coerce(float),
            vol.Optional(
                CONF_LONGITUDE,
                default=defaults.get(CONF_LONGITUDE, hass.config.longitude),
            ): vol.Coerce(float),
        }
    )


class PollenFranceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration Pollen France."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]

            session = async_get_clientsession(self.hass)
            api = PollenFranceApi(session=session, latitude=lat, longitude=lon)
            try:
                await api.fetch_all()
            except PollenFranceApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                unique_id = f"pollen_france_{lat:.4f}_{lon:.4f}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Pollen France ({lat:.2f}, {lon:.2f})",
                    data={
                        CONF_LATITUDE: lat,
                        CONF_LONGITUDE: lon,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(self.hass, user_input),
            errors=errors,
        )
