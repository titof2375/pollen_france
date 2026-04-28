"""API clients pour Pollen France.

Sources :
- Open-Meteo (CAMS/Copernicus) → 6 types, gratuit, sans clé, prioritaire
- SILAM THREDDS v6.1 (FMI)    → 7 types dont noisetier, gratuit, sans clé
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
    OPEN_METEO_URL,
    OPEN_METEO_VARS,
    OPEN_METEO_THRESHOLDS,
    SILAM_BASE_URL,
    SILAM_VARS,
    SILAM_THRESHOLDS,
    RISK_LEVELS,
)

_LOGGER = logging.getLogger(__name__)
TIMEOUT = aiohttp.ClientTimeout(total=30)


class PollenFranceApiError(Exception):
    """Erreur générique."""


class PollenFranceApi:
    """Client combinant Open-Meteo + SILAM."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        latitude: float,
        longitude: float,
    ) -> None:
        self._session = session
        self._lat = latitude
        self._lon = longitude

    async def fetch_all(self) -> dict[str, Any]:
        """Récupère et fusionne les données des deux sources."""
        open_meteo_data, silam_data = await asyncio.gather(
            self._fetch_open_meteo(),
            self._fetch_silam(),
            return_exceptions=True,
        )

        if isinstance(open_meteo_data, Exception):
            _LOGGER.warning("Open-Meteo indisponible : %s", open_meteo_data)
            open_meteo_data = {}

        if isinstance(silam_data, Exception):
            _LOGGER.warning("SILAM indisponible : %s", silam_data)
            silam_data = {}

        return self._merge(open_meteo_data, silam_data)

    # ── Open-Meteo ────────────────────────────────────────────────────────────

    async def _fetch_open_meteo(self) -> dict[str, Any]:
        """Interroge Open-Meteo et retourne les concentrations actuelles."""
        params = {
            "latitude": self._lat,
            "longitude": self._lon,
            "hourly": ",".join(OPEN_METEO_VARS.keys()),
            "forecast_days": "1",
            "timezone": "Europe/Paris",
        }
        try:
            async with self._session.get(
                OPEN_METEO_URL, params=params, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise PollenFranceApiError(f"Open-Meteo HTTP {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise PollenFranceApiError(f"Open-Meteo réseau : {err}") from err

        return self._parse_open_meteo(data)

    def _parse_open_meteo(self, data: dict) -> dict[str, Any]:
        """Extrait la valeur de l'heure courante pour chaque pollen."""
        result: dict[str, Any] = {}
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        # Heure courante Paris (format ISO sans secondes)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        # Cherche l'index le plus proche (heure courante ou dernière connue)
        idx = None
        for i, t in enumerate(times):
            if t.startswith(now_str[:13]):
                idx = i
                break
        if idx is None and times:
            idx = len(times) - 1  # fallback : dernière valeur
        if idx is None:
            return result

        for om_var, pollen_key in OPEN_METEO_VARS.items():
            values = hourly.get(om_var, [])
            if idx >= len(values):
                continue
            raw = values[idx]
            if raw is None:
                continue
            try:
                conc = float(raw)
            except (ValueError, TypeError):
                continue

            level = self._conc_to_level(pollen_key, conc, OPEN_METEO_THRESHOLDS)
            result[pollen_key] = {
                "niveau": level,
                "risque": RISK_LEVELS.get(level, "Inconnu"),
                "source": "Open-Meteo (CAMS)",
                "concentration_m3": round(conc, 2),
            }

        return result

    # ── SILAM THREDDS ─────────────────────────────────────────────────────────

    async def _fetch_silam(self) -> dict[str, Any]:
        """Interroge SILAM THREDDS pollen v6.1."""
        now_utc = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")
        params = [("var", v) for v in SILAM_VARS] + [
            ("latitude", self._lat),
            ("longitude", self._lon),
            ("time", now_utc),
            ("accept", "csv"),
        ]
        try:
            async with self._session.get(
                SILAM_BASE_URL, params=params, timeout=TIMEOUT
            ) as resp:
                if resp.status != 200:
                    raise PollenFranceApiError(f"SILAM HTTP {resp.status}")
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise PollenFranceApiError(f"SILAM réseau : {err}") from err

        return self._parse_silam(text)

    def _parse_silam(self, csv_text: str) -> dict[str, Any]:
        """Parse le CSV SILAM — prend la première ligne (altitude la plus basse)."""
        result: dict[str, Any] = {}
        if not csv_text.strip():
            return result
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            rows = list(reader)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("SILAM CSV parse error : %s", err)
            return result

        if not rows:
            return result

        # Première ligne = altitude la plus basse (sol, ~12.5 m)
        row = rows[0]

        for silam_var, pollen_key in SILAM_VARS.items():
            value = None
            for col in row:
                if silam_var in col:
                    value = row[col]
                    break
            if value is None:
                continue
            try:
                conc = float(value)
            except (ValueError, TypeError):
                continue

            level = self._conc_to_level(pollen_key, conc, SILAM_THRESHOLDS)
            result[pollen_key] = {
                "niveau": level,
                "risque": RISK_LEVELS.get(level, "Inconnu"),
                "source": "SILAM (FMI)",
                "concentration_m3": round(conc, 4),
            }

        return result

    # ── Fusion ────────────────────────────────────────────────────────────────

    def _merge(
        self,
        open_meteo: dict[str, Any],
        silam: dict[str, Any],
    ) -> dict[str, Any]:
        """Open-Meteo prioritaire pour les 6 types communs, SILAM pour noisetier."""
        merged: dict[str, Any] = {}

        # Tous les types connus
        for key in set(open_meteo) | set(silam):
            if key in open_meteo:
                entry = dict(open_meteo[key])
                # Enrichit avec la concentration SILAM si disponible
                if key in silam:
                    entry["concentration_m3_silam"] = silam[key].get("concentration_m3")
            else:
                entry = dict(silam[key])
            merged[key] = entry

        return merged

    # ── Utilitaire ────────────────────────────────────────────────────────────

    @staticmethod
    def _conc_to_level(
        pollen_key: str,
        conc: float,
        thresholds: dict[str, list[float]],
    ) -> int:
        """Convertit une concentration (grains/m³) en niveau de risque 0-5."""
        if conc <= 0:
            return 0
        seuils = thresholds.get(pollen_key, [1, 10, 30, 100, 300])
        for level, seuil in enumerate(seuils, start=1):
            if conc < seuil:
                return level - 1
        return 5
