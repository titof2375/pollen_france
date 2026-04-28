"""Intégration Pollen France.

Sources : Open-Meteo (CAMS) + SILAM THREDDS v6.1 (FMI)
Position : fixe (lat/lon) ou dynamique (person / device_tracker)
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE, CONF_TRACKER
from .coordinator import PollenFranceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migration des anciennes entrées vers le schéma actuel."""
    _LOGGER.debug("Migration Pollen France : v%s → v3", entry.version)

    new_data = dict(entry.data)

    # v1 avait un champ INSEE, on le supprime et on garde lat/lon
    new_data.pop("insee", None)

    # ajout des champs manquants
    new_data.setdefault(CONF_TRACKER, None)
    new_data.setdefault(CONF_NAME, f"Pollen France ({new_data.get(CONF_LATITUDE, ''):.2f}, {new_data.get(CONF_LONGITUDE, ''):.2f})")

    # lat/lon obligatoires : fallback sur la position HA si absents
    if CONF_LATITUDE not in new_data:
        new_data[CONF_LATITUDE] = hass.config.latitude
    if CONF_LONGITUDE not in new_data:
        new_data[CONF_LONGITUDE] = hass.config.longitude

    hass.config_entries.async_update_entry(entry, data=new_data, version=3)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    coordinator = PollenFranceCoordinator(
        hass=hass,
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        tracker=entry.data.get(CONF_TRACKER),
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
