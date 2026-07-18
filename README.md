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
- **Transparence du suivi** (depuis 2.3.0) : chaque capteur expose en attribut l'entité suivie et la position réellement utilisée, pour vérifier facilement que le suivi GPS fonctionne bien (voir ci-dessous)

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
| Tracker GPS | ❌ | Entité `person` ou `device_tracker` pour localisation dynamique — **si renseigné, aucune coordonnée à saisir** |
| Latitude / Longitude | ❌ | Utilisées uniquement en secours si aucun tracker n'est renseigné (laissez vide sinon) |
| Intervalle de rafraîchissement | ❌ | En minutes, 60 par défaut (minimum 5) |

---

## Attributs exposés par chaque capteur

| Attribut | Toujours présent | Description |
|----------|:---:|-------------|
| `risque` | ✅ | Libellé du niveau de risque (Nul → Très élevé) |
| `source` | ✅ | `open_meteo` ou `silam` |
| `concentration_m3` | ✅ | Concentration en grains/m³ |
| `concentration_m3_silam` | ❌ | Present uniquement si une valeur SILAM est disponible en complément |
| `tracker_entity` | ❌ | Entité `person`/`device_tracker` suivie — **absent si l'instance utilise une position fixe** |
| `latitude_suivie` / `longitude_suivie` | ✅ | Position réellement utilisée pour la dernière requête (celle du tracker si configuré, sinon la position fixe) |

**Comment vérifier que le suivi GPS fonctionne** : ouvre l'entité dans Développeur → États et regarde `tracker_entity` (doit afficher ton `person.xxx`/`device_tracker.xxx`) et `latitude_suivie`/`longitude_suivie` (doit correspondre à ta position actuelle, pas à celle de la maison).

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
| 2.4.2 | Fix réel de la 2.4.1 (le correctif n'avait pas été appliqué) : latitude/longitude sont désormais vraiment optionnelles dans le formulaire |
| 2.4.1 | (retiré — correctif incomplet) |
| 2.4.0 | Intervalle de rafraîchissement configurable (`scan_interval`) |
| 2.3.0 | Nouveaux attributs `tracker_entity`, `latitude_suivie`, `longitude_suivie` pour vérifier le suivi GPS |
| 2.2.3 | Correctifs mineurs |
| 2.2.2 | Correctifs mineurs |
| 2.2.1 | Fix unique_id et nom appareil pour instances multiples au même endroit |
| 2.2.0 | Noms personnalisés par instance |
| 2.1.1 | Fix migration config |
| 2.1.0 | Suivi GPS dynamique via person/device_tracker |
| 2.0.0 | Refonte complète : Open-Meteo + SILAM, noisetier inclus |
| 1.0.0 | Version initiale |
