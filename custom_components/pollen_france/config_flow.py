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
from homeassistant.helpers import config_validation as cv

from .api import PollenFranceApi, PollenFranceApiError
from .const import DOMAIN, CONF_INSEE, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)


def _schema(hass: HomeAssistant, defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_INSEE,
                default=defaults.get(CONF_INSEE, ""),
            ): str,
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

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            insee = user_input[CONF_INSEE].strip()
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]

            # Vérifie que le code INSEE est valide (5 chiffres)
            if not insee.isdigit() or len(insee) != 5:
                errors[CONF_INSEE] = "invalid_insee"
            else:
                # Teste l'API
                session = async_get_clientsession(self.hass)
                api = PollenFranceApi(
                    session=session,
                    insee=insee,
                    latitude=lat,
                    longitude=lon,
                )
                try:
                    await api.fetch_all()
                except PollenFranceApiError:
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    errors["base"] = "unknown"
                else:
                    # Évite les doublons
                    await self.async_set_unique_id(f"pollen_france_{insee}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Pollen France – {insee}",
                        data={
                            CONF_INSEE: insee,
                            CONF_LATITUDE: lat,
                            CONF_LONGITUDE: lon,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(self.hass, user_input),
            errors=errors,
            description_placeholders={
                "example_insee": "87085",
                "example_city": "Limoges",
            },
        )
