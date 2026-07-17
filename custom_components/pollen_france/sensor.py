"""Capteurs pollen pour Pollen France."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, ATTR_RISK, ATTR_SOURCE, ATTR_CONCENTRATION
from .coordinator import PollenFranceCoordinator

_LOGGER = logging.getLogger(__name__)

POLLEN_LABELS: dict[str, str] = {
    "graminees": "Graminées",
    "bouleau":   "Bouleau",
    "aulne":     "Aulne",
    "noisetier": "Noisetier",
    "armoise":   "Armoise",
    "ambroisie": "Ambroisie",
    "olivier":   "Olivier",
}

POLLEN_ICONS: dict[str, str] = {
    "graminees": "mdi:grass",
    "bouleau":   "mdi:tree",
    "aulne":     "mdi:tree-outline",
    "noisetier": "mdi:tree",
    "armoise":   "mdi:flower-pollen",
    "ambroisie": "mdi:flower-pollen-outline",
    "olivier":   "mdi:olive",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PollenFranceCoordinator = hass.data[DOMAIN][entry.entry_id]
    instance_name = entry.data.get(CONF_NAME, entry.title)

    await coordinator.async_config_entry_first_refresh()

    # FIX: on crée TOUJOURS les 7 capteurs connus, quel que soit le contenu
    # du premier refresh. Si l'API a échoué/été rate-limitée au démarrage
    # (coordinator.data == {}), les entités existent quand même et passent
    # simplement à "unavailable" via PollenSensor.available, au lieu de ne
    # jamais être créées du tout.
    entities = [
        PollenSensor(
            coordinator=coordinator,
            pollen_key=key,
            instance_name=instance_name,
            entry_id=entry.entry_id,
        )
        for key in POLLEN_LABELS
    ]
    async_add_entities(entities)


class PollenSensor(CoordinatorEntity[PollenFranceCoordinator], SensorEntity):
    """Capteur pour un type de pollen."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PollenFranceCoordinator,
        pollen_key: str,
        instance_name: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._pollen_key = pollen_key
        # Unique_id basé sur entry_id → pas de conflit entre instances
        self._attr_unique_id = f"{entry_id}_{pollen_key}"
        self._attr_name = POLLEN_LABELS.get(pollen_key, pollen_key.capitalize())
        self._attr_icon = POLLEN_ICONS.get(pollen_key, "mdi:flower-pollen")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=instance_name,
            manufacturer="Open-Meteo / SILAM (FMI)",
            model="Pollen monitoring",
            entry_type="service",
        )

    @property
    def _data(self) -> dict[str, Any] | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._pollen_key)

    @property
    def native_value(self) -> int | None:
        if self._data is None:
            return None
        return self._data.get("niveau")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._data is None:
            return {}
        attrs: dict[str, Any] = {
            ATTR_RISK:          self._data.get("risque"),
            ATTR_SOURCE:        self._data.get("source"),
            ATTR_CONCENTRATION: self._data.get("concentration_m3"),
        }
        if "concentration_m3_silam" in self._data:
            attrs["concentration_m3_silam"] = self._data["concentration_m3_silam"]
        return attrs

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self._pollen_key in self.coordinator.data
        )
