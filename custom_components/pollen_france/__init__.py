"""Intégration Pollen France.

Combine les données de :
- Recosanté (Atmo France) — niveaux officiels, ~14 types de pollen
- SILAM THREDDS (FMI) — concentrations scientifiques, types complémentaires
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_INSEE, CONF_LATITUDE, CONF_LONGITUDE
from .coordinator import PollenFranceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialise l'intégration depuis une entrée de configuration."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PollenFranceCoordinator(
        hass=hass,
        insee=entry.data[CONF_INSEE],
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
