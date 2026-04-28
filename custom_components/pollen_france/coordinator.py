"""DataUpdateCoordinator pour Pollen France."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PollenFranceApi, PollenFranceApiError
from .const import DOMAIN, UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class PollenFranceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinateur de mise à jour des données pollen."""

    def __init__(
        self,
        hass: HomeAssistant,
        insee: str,
        latitude: float,
        longitude: float,
    ) -> None:
        self._insee = insee
        self._latitude = latitude
        self._longitude = longitude

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{insee}",
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Récupère les données depuis les deux API."""
        session: aiohttp.ClientSession = async_get_clientsession(self.hass)
        api = PollenFranceApi(
            session=session,
            insee=self._insee,
            latitude=self._latitude,
            longitude=self._longitude,
        )
        try:
            data = await api.fetch_all()
        except PollenFranceApiError as err:
            raise UpdateFailed(f"Erreur API Pollen France : {err}") from err

        if not data:
            _LOGGER.warning(
                "Aucune donnée pollen récupérée pour INSEE=%s (lat=%.4f, lon=%.4f)",
                self._insee,
                self._latitude,
                self._longitude,
            )

        return data
