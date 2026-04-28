"""API clients for Pollen France integration.

Sources :
- Recosanté (Atmo France officiel) → niveaux de risque 0-5 pour ~14 types
- SILAM THREDDS (FMI) → concentrations scientifiques en particules/m³
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .const import (
    RECOSVANTE_URL,
    RECOSVANTE_POLLEN_MAP,
    SILAM_BASE_URL,
    SILAM_VARS,
    SILAM_VAR_NAMES,
    SILAM_THRESHOLDS,
    RISK_LEVELS,
)

_LOGGER = logging.getLogger(__name__)

TIMEOUT = aiohttp.ClientTimeout(total=30)


class PollenFranceApiError(Exception):
    """Erreur générique de l'API Pollen France."""


class PollenFranceApi:
    """Client API combinant Recosanté + SILAM."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        insee: str,
        latitude: float,
        longitude: float,
    ) -> None:
        self._session = session
        self._insee = insee
        self._latitude = latitude
        self._longitude = longitude

    # ─────────────────────────────────────────────────────────────────────────
    # Point d'entrée principal
    # ─────────────────────────────────────────────────────────────────────────

    async def fetch_all(self) -> dict[str, Any]:
        """Récupère et fusionne les données Recosanté + SILAM."""
        recosvante_data, silam_data = await asyncio.gather(
            self._fetch_recosvante(),
            self._fetch_silam(),
            return_exceptions=True,
        )

        if isinstance(recosvante_data, Exception):
            _LOGGER.warning("Recosanté unavailable: %s", recosvante_data)
            recosvante_data = {}

        if isinstance(silam_data, Exception):
            _LOGGER.warning("SILAM unavailable: %s", silam_data)
            silam_data = {}

        return self._merge(recosvante_data, silam_data)

    # ─────────────────────────────────────────────────────────────────────────
    # Recosanté
    # ─────────────────────────────────────────────────────────────────────────

    async def _fetch_recosvante(self) -> dict[str, Any]:
        """Interroge l'API Recosanté et retourne les niveaux par type de pollen."""
        params = {"insee": self._insee}
        try:
            async with self._session.get(
                RECOSVANTE_URL, params=params, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise PollenFranceApiError(
                        f"Recosanté HTTP {resp.status}"
                    )
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise PollenFranceApiError(f"Recosanté réseau : {err}") from err

        return self._parse_recosvante(data)

    def _parse_recosvante(self, data: dict) -> dict[str, Any]:
        """Extrait les niveaux de pollen de la réponse Recosanté."""
        result: dict[str, Any] = {}

        # La réponse Recosanté contient un tableau "data" avec les indicateurs
        indicators = data.get("data", [])
        for item in indicators:
            # On cherche l'indicateur pollen
            label = str(item.get("label", "")).lower()
            if "pollen" not in label and item.get("type") != "pollen":
                continue

            # Sous-données par type de pollen
            sub_values = item.get("values", [])
            for sub in sub_values:
                pollen_name_raw = str(sub.get("label", "")).lower()
                # Normalisation des accents
                pollen_name = self._normalize_name(pollen_name_raw)
                mapped = RECOSVANTE_POLLEN_MAP.get(pollen_name)
                if not mapped:
                    # Essai direct
                    for key in RECOSVANTE_POLLEN_MAP:
                        if key in pollen_name or pollen_name in key:
                            mapped = RECOSVANTE_POLLEN_MAP[key]
                            break
                if not mapped:
                    continue

                level = sub.get("value")
                if level is None:
                    level = sub.get("level")
                if level is None:
                    continue

                try:
                    level_int = int(level)
                except (ValueError, TypeError):
                    continue

                result[mapped] = {
                    "niveau": level_int,
                    "risque": RISK_LEVELS.get(level_int, "Inconnu"),
                    "source": "Recosanté (Atmo France)",
                    "concentration_m3": None,
                }

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # SILAM THREDDS
    # ─────────────────────────────────────────────────────────────────────────

    async def _fetch_silam(self) -> dict[str, Any]:
        """Interroge le THREDDS SILAM et retourne les concentrations."""
        now_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")

        params = {
            "var": SILAM_VARS,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "time": now_utc,
            "vertCoord": "0",
            "accept": "csv",
        }

        try:
            async with self._session.get(
                SILAM_BASE_URL, params=params, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise PollenFranceApiError(
                        f"SILAM HTTP {resp.status}"
                    )
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise PollenFranceApiError(f"SILAM réseau : {err}") from err

        return self._parse_silam(text)

    def _parse_silam(self, csv_text: str) -> dict[str, Any]:
        """Parse le CSV SILAM et retourne les concentrations par type."""
        result: dict[str, Any] = {}

        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("SILAM CSV parse error: %s", err)
            return result

        if not rows:
            return result

        # Prendre la dernière ligne (données les plus récentes)
        row = rows[-1]

        for var, pollen_key in SILAM_VAR_NAMES.items():
            # Le nom de colonne dans le CSV peut varier légèrement
            value = None
            for col in row:
                if var.lower() in col.lower():
                    value = row[col]
                    break

            if value is None:
                continue

            try:
                conc = float(value)
            except (ValueError, TypeError):
                continue

            # Conversion en niveau 0-5
            level = self._concentration_to_level(pollen_key, conc)

            result[pollen_key] = {
                "niveau": level,
                "risque": RISK_LEVELS.get(level, "Inconnu"),
                "source": "SILAM (FMI)",
                "concentration_m3": round(conc, 2),
            }

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Fusion des deux sources
    # ─────────────────────────────────────────────────────────────────────────

    def _merge(
        self,
        recosvante: dict[str, Any],
        silam: dict[str, Any],
    ) -> dict[str, Any]:
        """Fusionne les données : Recosanté prioritaire, SILAM en complément."""
        merged: dict[str, Any] = {}

        # Tous les pollens connus des deux sources
        all_keys = set(recosvante.keys()) | set(silam.keys())

        for key in all_keys:
            if key in recosvante:
                entry = dict(recosvante[key])
                # Ajoute la concentration SILAM si disponible
                if key in silam and silam[key].get("concentration_m3") is not None:
                    entry["concentration_m3"] = silam[key]["concentration_m3"]
                merged[key] = entry
            elif key in silam:
                merged[key] = dict(silam[key])

        return merged

    # ─────────────────────────────────────────────────────────────────────────
    # Utilitaires
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Supprime les accents courants pour normaliser les noms."""
        replacements = {
            "é": "e", "è": "e", "ê": "e", "ë": "e",
            "à": "a", "â": "a", "ä": "a",
            "ô": "o", "ö": "o",
            "ù": "u", "û": "u", "ü": "u",
            "î": "i", "ï": "i",
            "ç": "c",
        }
        for accented, plain in replacements.items():
            name = name.replace(accented, plain)
        return name

    @staticmethod
    def _concentration_to_level(pollen_key: str, conc: float) -> int:
        """Convertit une concentration (p/m³) en niveau de risque 0-5."""
        thresholds = SILAM_THRESHOLDS.get(pollen_key, [0, 10, 50, 150, 500])
        if conc <= 0:
            return 0
        for i, threshold in enumerate(reversed(thresholds)):
            if conc >= threshold:
                return len(thresholds) - i
        return 1
