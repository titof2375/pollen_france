# Pollen France — Intégration HACS pour Home Assistant

Suivi des pollens en France via deux sources complémentaires :
- **Open-Meteo** (CAMS/Copernicus) — données horaires, 6 types de pollens
- **SILAM THREDDS v6.1** (FMI) — modèle européen, inclut le **noisetier**

Aucune clé API requise. Données gratuites et libres.

---

## Pollens suivis

| Pollen | Source principale |
|--------|------------------|
| Graminées | Open-Meteo |
| Bouleau | Open-Meteo |
| Aulne | Open-Meteo |
| Armoise | Open-Meteo |
| Olivier | Open-Meteo |
| Ambroisie | Open-Meteo |
| **Noisetier** | **SILAM** (uniquement) |

---

## Fonctionnalités

- **7 capteurs** par instance (un par type de pollen)
- Niveau de risque **0 à 5** (Nul → Très élevé) selon les seuils EAN
- Attribut **concentration** en grains/m³
- Attribut **source** (open_meteo ou silam)
- **Rafraîchissement toutes les heures**
- **Suivi GPS dynamique** : utilisez votre téléphone (entité `person` ou `device_tracker`) pour suivre les pollens en vacances
- **Plusieurs instances** : une par personne ou par lieu (Maison, Travail, Vacances…)

---

## Installation via HACS

1. HACS → ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/titof2375/pollen_france`
   Catégorie : **Intégration**
3. Installer **Pollen France**
4. **Redémarrer Home Assistant**
5. Paramètres → Intégrations → **+ Ajouter** → chercher **Pollen France**

---

## Configuration

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| Nom | ✅ | Nom de l'instance (ex : Maison, Christophe…) |
| Latitude | ✅ | Pré-remplie avec la position de votre HA |
| Longitude | ✅ | Pré-remplie avec la position de votre HA |
| Tracker GPS | ❌ | Entité `person` ou `device_tracker` pour localisation dynamique |

---

## Niveaux de risque

| Niveau | Libellé |
|--------|---------|
| 0 | Nul |
| 1 | Très faible |
| 2 | Faible |
| 3 | Moyen |
| 4 | Élevé |
| 5 | Très élevé |

Seuils basés sur les recommandations du **Réseau Européen d'Aéroallergologie (EAN)**.

---

## Versions

| Version | Notes |
|---------|-------|
| 2.2.1 | Fix unique_id et nom appareil pour instances multiples au même endroit |
| 2.2.0 | Noms personnalisés par instance |
| 2.1.1 | Fix migration config |
| 2.1.0 | Suivi GPS dynamique via person/device_tracker |
| 2.0.0 | Refonte complète : Open-Meteo + SILAM, noisetier inclus |
| 1.0.0 | Version initiale |
