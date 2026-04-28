"""Config flow pour Pollen France."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api import PollenFranceApi, PollenFranceApiError
from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, CONF_TRACKER

_LOGGER = logging.getLogger(__name__)


class PollenFranceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration Pollen France."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            tracker = user_input.get(CONF_TRACKER) or None
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]

            # Si un tracker est sélectionné, tente de lire sa position
            if tracker:
                state = self.hass.states.get(tracker)
                if state:
                    t_lat = state.attributes.get("latitude")
                    t_lon = state.attributes.get("longitude")
                    if t_lat is not None and t_lon is not None:
                        try:
                            lat = float(t_lat)
                            lon = float(t_lon)
                        except (ValueError, TypeError):
                            pass

            session = async_get_clientsession(self.hass)
            api = PollenFranceApi(session=session, latitude=lat, longitude=lon)
            try:
                await api.fetch_all()
            except PollenFranceApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                unique_id = tracker or f"pollen_france_{lat:.4f}_{lon:.4f}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = tracker if tracker else f"Pollen France ({lat:.2f}, {lon:.2f})"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_LATITUDE:  lat,
                        CONF_LONGITUDE: lon,
                        CONF_TRACKER:   tracker,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_TRACKER): selector.selector(
                    {
                        "entity": {
                            "domain": ["person", "device_tracker"],
                            "multiple": False,
                        }
                    }
                ),
                vol.Optional(
                    CONF_LATITUDE,
                    default=self.hass.config.latitude,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_LONGITUDE,
                    default=self.hass.config.longitude,
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={},
        )
