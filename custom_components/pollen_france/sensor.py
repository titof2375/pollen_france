"""Capteurs pollen pour l'intégration Pollen France."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_INSEE,
    ATTR_LEVEL,
    ATTR_RISK,
    ATTR_SOURCE,
    ATTR_CONCENTRATION,
    RISK_LEVELS,
)
from .coordinator import PollenFranceCoordinator

_LOGGER = logging.getLogger(__name__)

# Noms lisibles pour chaque type de pollen
POLLEN_LABELS: dict[str, str] = {
    "graminees": "Graminées",
    "bouleau": "Bouleau",
    "aulne": "Aulne",
    "armoise": "Armoise",
    "ambroisie": "Ambroisie",
    "olivier": "Olivier",
    "noisetier": "Noisetier",
    "platane": "Platane",
    "chene": "Chêne",
    "frene": "Frêne",
    "peuplier": "Peuplier",
    "charme": "Charme",
    "cypres": "Cyprès",
    "urticacees": "Urticacées",
}

# Icônes par type de pollen
POLLEN_ICONS: dict[str, str] = {
    "graminees": "mdi:grass",
    "bouleau": "mdi:tree",
    "aulne": "mdi:tree-outline",
    "armoise": "mdi:flower-pollen",
    "ambroisie": "mdi:flower-pollen-outline",
    "olivier": "mdi:olive",
    "noisetier": "mdi:tree",
    "platane": "mdi:tree",
    "chene": "mdi:tree",
    "frene": "mdi:tree-outline",
    "peuplier": "mdi:tree",
    "charme": "mdi:tree-outline",
    "cypres": "mdi:pine-tree",
    "urticacees": "mdi:flower-pollen",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée les capteurs pollen à partir d'une entrée de configuration."""
    coordinator: PollenFranceCoordinator = hass.data[DOMAIN][entry.entry_id]
    insee = entry.data[CONF_INSEE]

    # Attendre le premier refresh pour connaître les types disponibles
    await coordinator.async_config_entry_first_refresh()

    entities: list[PollenSensor] = []
    for pollen_key in coordinator.data or {}:
        entities.append(
            PollenSensor(
                coordinator=coordinator,
                pollen_key=pollen_key,
                insee=insee,
                entry_id=entry.entry_id,
            )
        )

    async_add_entities(entities)


class PollenSensor(CoordinatorEntity[PollenFranceCoordinator], SensorEntity):
    """Capteur pour un type de pollen."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PollenFranceCoordinator,
        pollen_key: str,
        insee: str,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._pollen_key = pollen_key
        self._insee = insee
        self._attr_unique_id = f"pollen_france_{insee}_{pollen_key}"
        self._attr_name = POLLEN_LABELS.get(pollen_key, pollen_key.capitalize())
        self._attr_icon = POLLEN_ICONS.get(pollen_key, "mdi:flower-pollen")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"pollen_france_{insee}")},
            name=f"Pollen France {insee}",
            manufacturer="Recosanté / SILAM (FMI)",
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
        """Retourne le niveau de risque (0-5)."""
        if self._data is None:
            return None
        return self._data.get("niveau")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Attributs supplémentaires."""
        if self._data is None:
            return {}
        return {
            ATTR_RISK: self._data.get("risque"),
            ATTR_SOURCE: self._data.get("source"),
            ATTR_CONCENTRATION: self._data.get("concentration_m3"),
            "insee": self._insee,
        }

    @property
    def available(self) -> bool:
        """Disponible si le coordinateur a des données pour ce pollen."""
        return (
            super().available
            and self.coordinator.data is not None
            and self._pollen_key in self.coordinator.data
        )
