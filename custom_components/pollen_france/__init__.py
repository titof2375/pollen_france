"""Intégration Pollen France.

Combine :
- Open-Meteo (CAMS/Copernicus) — 6 types, gratuit, sans clé
- SILAM THREDDS v6.1 (FMI)    — 7 types dont noisetier, gratuit, sans clé
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_LATITUDE, CONF_LONGITUDE
from .coordinator import PollenFranceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialise l'intégration depuis une entrée de configuration."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PollenFranceCoordinator(
        hass=hass,
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
