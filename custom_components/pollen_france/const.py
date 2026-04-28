"""Constants for the Pollen France integration."""

DOMAIN = "pollen_france"

CONF_INSEE = "insee"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

# Update interval in hours
UPDATE_INTERVAL_HOURS = 3

# ── Recosanté API (Atmo France officiel) ──────────────────────────────────────
RECOSVANTE_URL = "https://api.recosante.beta.gouv.fr/v1/"

# ── SILAM THREDDS (FMI, données scientifiques supplémentaires) ────────────────
SILAM_BASE_URL = (
    "https://thredds.silam.fmi.fi/thredds/ncss/grid"
    "/silam_europe_v5_9_1/silam_europe_v5_9_1_best.ncd"
)

# Variables SILAM disponibles (concentration en particules/m³)
SILAM_VARS = [
    "cnc_BIRCH_m22",     # Bouleau
    "cnc_ALDER_m22",     # Aulne
    "cnc_GRASS_m22",     # Graminées
    "cnc_OLIVE_m22",     # Olivier
    "cnc_RAGWEED_m22",   # Ambroisie
    "cnc_MUGWORT_m22",   # Armoise
]

# Mapping variable SILAM → nom lisible
SILAM_VAR_NAMES = {
    "cnc_BIRCH_m22": "bouleau",
    "cnc_ALDER_m22": "aulne",
    "cnc_GRASS_m22": "graminees",
    "cnc_OLIVE_m22": "olivier",
    "cnc_RAGWEED_m22": "ambroisie",
    "cnc_MUGWORT_m22": "armoise",
}

# Mapping source Recosanté → clé normalisée
RECOSVANTE_POLLEN_MAP = {
    "graminees": "graminees",
    "bouleau": "bouleau",
    "aulne": "aulne",
    "armoise": "armoise",
    "ambroisie": "ambroisie",
    "olivier": "olivier",
    "noisetier": "noisetier",
    "platane": "platane",
    "chene": "chene",
    "frene": "frene",
    "peuplier": "peuplier",
    "charme": "charme",
    "cypres": "cypres",
    "urticacees": "urticacees",
}

# Niveaux de risque pollen (0-5)
RISK_LEVELS = {
    0: "Nul",
    1: "Très faible",
    2: "Faible",
    3: "Moyen",
    4: "Élevé",
    5: "Très élevé",
}

# Seuils SILAM → niveau risque (particules/m³)
# Basés sur les seuils EAN (European Aeroallergen Network)
SILAM_THRESHOLDS = {
    "bouleau": [0, 10, 80, 200, 1500],     # p/m³
    "aulne": [0, 10, 50, 200, 1000],
    "graminees": [0, 10, 30, 50, 150],
    "olivier": [0, 10, 50, 200, 500],
    "ambroisie": [0, 5, 10, 30, 100],
    "armoise": [0, 10, 30, 100, 300],
}

# Attributs de données
ATTR_LEVEL = "niveau"
ATTR_RISK = "risque"
ATTR_SOURCE = "source"
ATTR_UPDATED = "mis_a_jour"
ATTR_CONCENTRATION = "concentration_m3"
