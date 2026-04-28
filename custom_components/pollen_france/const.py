"""Constants for the Pollen France integration."""

DOMAIN = "pollen_france"

CONF_LATITUDE  = "latitude"
CONF_LONGITUDE = "longitude"
CONF_TRACKER   = "tracker"        # entité person/device_tracker (optionnel)

UPDATE_INTERVAL_MINUTES = 60      # refresh toutes les heures

# ── Open-Meteo Air Quality (CAMS/Copernicus, gratuit, sans clé) ───────────────
OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

OPEN_METEO_VARS = {
    "alder_pollen":   "aulne",
    "birch_pollen":   "bouleau",
    "grass_pollen":   "graminees",
    "mugwort_pollen": "armoise",
    "olive_pollen":   "olivier",
    "ragweed_pollen": "ambroisie",
}

# ── SILAM THREDDS pollen v6.1 (FMI, gratuit, sans clé) ───────────────────────
SILAM_BASE_URL = (
    "https://thredds.silam.fmi.fi/thredds/ncss/grid"
    "/silam_europe_pollen_v6_1/silam_europe_pollen_v6_1_best.ncd"
)

SILAM_VARS = {
    "cnc_POLLEN_HAZEL_m23":   "noisetier",
    "cnc_POLLEN_BIRCH_m22":   "bouleau",
    "cnc_POLLEN_ALDER_m22":   "aulne",
    "cnc_POLLEN_GRASS_m32":   "graminees",
    "cnc_POLLEN_MUGWORT_m18": "armoise",
    "cnc_POLLEN_OLIVE_m20":   "olivier",
    "cnc_POLLEN_RAGWEED_m18": "ambroisie",
}

# Niveaux de risque (0-5)
RISK_LEVELS = {
    0: "Nul",
    1: "Très faible",
    2: "Faible",
    3: "Moyen",
    4: "Élevé",
    5: "Très élevé",
}

# Seuils grains/m³ → niveau 1-5 (EAN)
SILAM_THRESHOLDS: dict[str, list[float]] = {
    "bouleau":   [1,   10,  80,  200, 1500],
    "aulne":     [1,   10,  50,  200, 1000],
    "graminees": [1,   10,  30,   50,  150],
    "noisetier": [1,   10,  50,  150,  500],
    "armoise":   [1,   10,  30,  100,  300],
    "olivier":   [1,   10,  50,  200,  500],
    "ambroisie": [0.5,  5,  10,   30,  100],
}

OPEN_METEO_THRESHOLDS = SILAM_THRESHOLDS

ATTR_RISK          = "risque"
ATTR_SOURCE        = "source"
ATTR_CONCENTRATION = "concentration_m3"
