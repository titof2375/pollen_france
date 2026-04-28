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
from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE, CONF_TRACKER, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class PollenFranceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinateur de mise à jour — position fixe ou suivant un tracker."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        tracker: str | None = None,
    ) -> None:
        self._default_lat = latitude
        self._default_lon = longitude
        self._tracker = tracker

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{tracker or f'{latitude:.4f}_{longitude:.4f}'}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    def _get_location(self) -> tuple[float, float]:
        """Retourne lat/lon : depuis le tracker si défini, sinon position fixe."""
        if self._tracker:
            state = self.hass.states.get(self._tracker)
            if state:
                lat = state.attributes.get("latitude")
                lon = state.attributes.get("longitude")
                if lat is not None and lon is not None:
                    try:
                        return float(lat), float(lon)
                    except (ValueError, TypeError):
                        pass
            _LOGGER.warning(
                "Pollen France : impossible de lire la position de %s, "
                "utilisation de la position par défaut.",
                self._tracker,
            )
        return self._default_lat, self._default_lon

    async def _async_update_data(self) -> dict[str, Any]:
        """Récupère les données pollen pour la position courante."""
        lat, lon = self._get_location()
        session: aiohttp.ClientSession = async_get_clientsession(self.hass)
        api = PollenFranceApi(session=session, latitude=lat, longitude=lon)
        try:
            data = await api.fetch_all()
        except PollenFranceApiError as err:
            raise UpdateFailed(f"Erreur API Pollen France : {err}") from err

        if not data:
            _LOGGER.warning(
                "Aucune donnée pollen récupérée (lat=%.4f, lon=%.4f)", lat, lon
            )

        return data
