# HydraXAI France 🌊 — Cartographie explicable du risque inondation par commune

**👉 Démo en ligne : [hydraxai-france.streamlit.app](https://hydraxai-france.streamlit.app)**

Modèle de machine learning géospatial qui estime, pour chaque commune de France métropolitaine, la probabilité d'une **exposition forte aux inondations**, et **explique** ses prédictions avec SHAP.

> ⚠️ Projet portfolio à visée pédagogique. Il ne remplace pas les documents officiels (Géorisques, PPRI, DICRIM).

---

## 🎯 Problématique

Les arrêtés de catastrophe naturelle (CatNat) « inondation » montrent que certaines communes sont reconnues sinistrées bien plus souvent que d'autres.
**Peut-on expliquer ces différences à partir du terrain (relief, humidité des sols) et des pluies extrêmes ? Et quelles variables comptent le plus ?**

## 📊 Données

| Donnée | Source | Traitement |
|---|---|---|
| Arrêtés CatNat inondation | Base GASPAR (Géorisques), via BigQuery | Libellés « inondations et/ou coulées de boue » et « inondations remontée nappe » ; arrêtés distincts par commune (3 347 doublons retirés) |
| Historique des communes | INSEE, Code officiel géographique 2026 (mouvements des communes) | 102 anciens codes (communes fusionnées) rattachés à leur commune actuelle |
| Humidité des sols (SWI) | Météo-France, grille SIM (8 981 points, maille 8 km), 1982 → aujourd'hui | Plus proche voisin depuis le centre de chaque commune (Lambert-93, 10 km max) |
| Pluies quotidiennes | Météo-France, SIM2 quotidien (1982 → 2025) | Par point de grille : pluie max d'un jour, jours ≥ 50 mm, cumul annuel |
| Relief | IGN, RGE ALTI (API altimétrique de la Géoplateforme) | 5 points par commune (centre + 4 points à 1 km) |
| Centres des communes | API Découpage administratif (geo.api.gouv.fr) | Coordonnées WGS84 |

**Périmètre :** les 34 746 communes actuelles de France métropolitaine, y compris les 388 qui n'ont jamais eu d'arrêté inondation.

## 🧭 Méthode

**1. Cible.** La médiane est de 3 arrêtés par commune et le 75ᵉ percentile de 5.
→ `risque_fort = 1` si la commune compte **6 arrêtés ou plus** (22 % des communes).

**2. Variables (12)**
- SWI : `swi_moyen`, `swi_max`, `swi_p90`, `part_mois_sature` (part des mois avec SWI ≥ 1)
- Relief : `altitude`, `denivele_local`, `pente_max_pct`, `position_relative` (indice proche du TPI : centre − moyenne des voisins)
- Pluies extrêmes : `pluie_max_jour_moy`, `pluie_max_jour_abs`, `nb_jours_50mm_an`, `cumul_annuel_moy`

Les coordonnées ne sont **pas** utilisées comme variables : le modèle doit apprendre du terrain, pas de la position sur la carte.

**3. Modèle.** XGBoost (300 arbres, profondeur 4), **sans pondération des classes**. Avec `scale_pos_weight`, le classement des communes était le même, mais les probabilités étaient environ deux fois trop élevées (moyenne 0,41 pour une prévalence de 0,22). Sans pondération, elles sont **calibrées** : sur 100 communes prédites à 30 %, environ 30 ont réellement 6 arrêtés ou plus.

**4. Validation spatiale.** `GroupKFold` par département : le modèle est toujours testé sur des départements qu'il n'a jamais vus. Les probabilités affichées dans l'app sont ces prédictions hors échantillon.

## 📈 Résultats (v3)

| Métrique | Validation aléatoire | **Validation spatiale** | Hasard |
|---|---|---|---|
| ROC-AUC | 0,809 | **0,730** | 0,5 |
| PR-AUC | 0,597 | **0,478** | 0,22 |
| Score de Brier | 0,129 | **0,148** | 0,172 |

- La validation aléatoire **surestime** la performance : les communes voisines se ressemblent (autocorrélation spatiale).
- En validation spatiale, la PR-AUC est **plus du double** du hasard.
- Ajouter les pluies extrêmes améliore la PR-AUC dans chacun des 5 groupes de départements (notebook 02).

### Évolution du modèle (validation spatiale)

| Version | Changement | ROC-AUC | PR-AUC |
|---|---|---|---|
| v1 | SWI + relief (8 variables) | 0,717 | 0,462 |
| v2 | + pluies extrêmes (12 variables) | 0,731 | 0,496 |
| v3 | cible corrigée, probabilités calibrées | 0,730 | 0,478 |

La v3 n'est pas « moins bonne » que la v2 : la cible a changé (arrêtés dédoublonnés, communes fusionnées, 22 % de communes positives au lieu de 23,5 %), donc les PR-AUC ne se comparent pas directement. Le ROC-AUC, lui, reste stable.

## 🔍 Explicabilité (SHAP)

Les valeurs SHAP sont calculées **hors échantillon** : chaque commune est expliquée par le modèle qui l'a prédite, sans avoir vu son département. L'app affiche ces contributions commune par commune.

- **Altitude** (variable la plus importante) : les communes basses sont plus exposées.
- **Pluies extrêmes** : plus les pluies journalières maximales sont fortes et les jours à 50 mm fréquents, plus le risque augmente. Cela confirme l'hypothèse de la v1 (sols souvent secs mais saturés ponctuellement = épisodes intenses).
- **SWI** : un SWI moyen faible reste associé à un risque plus fort.
- **Dénivelé local** : un relief marqué augmente le risque (la cible inclut les coulées de boue).
- `pente_max_pct` et `position_relative` apportent peu.

La carte des probabilités fait ressortir le pourtour méditerranéen, le Sud-Ouest et les grands axes de vallées.

## ⚠️ Limites

- **La cible mesure les inondations *reconnues*** : un arrêté CatNat n'existe que si la commune en fait la demande.
- **Les erreurs sont regroupées par région** (analyse du modèle v1), ce qui indique des informations régionales manquantes.
- Une commune nouvelle cumule les arrêtés de ses anciennes communes, et une grande commune a mécaniquement plus de chances d'en avoir.
- Le centre de la commune ne représente pas toute sa surface.
- Les variables de SWI sont corrélées entre elles : leurs contributions SHAP se lisent ensemble.
- SHAP explique le modèle, pas une causalité physique.

## 🚀 Suite

- Ajouter la **distance au cours d'eau** et la taille du bassin versant
- Valider sur des blocs spatiaux plus grands (régions) pour mesurer la fuite entre départements voisins
- Tester une régression sur le **nombre** d'arrêtés

## 🗂️ Structure du dépôt

```
hydraxai-france/
├── app/
│   ├── app.py               # application Streamlit
│   ├── carte_risque_v1.html # carte interactive de la v1
│   └── requirements.txt     # dépendances de l'app
├── data/                    # tables préparées (parquet)
├── notebooks/
│   ├── 01_exploration_catnat.ipynb       # v1 : cible, SWI, relief, modèle, SHAP, cartes
│   ├── 02_pluies_extremes.ipynb          # v2 : ajout des pluies extrêmes (SIM2 quotidien)
│   └── 03_cible_calibration_shap.ipynb   # v3 : cible corrigée, calibration, SHAP par commune
└── requirements.txt         # environnement complet du projet
```

## ▶️ Lancer le projet en local

```bash
git clone https://github.com/Asma-Iam/hydraxai-france.git
cd hydraxai-france
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

## 🛠️ Stack

Python · pandas · GeoPandas · BigQuery · XGBoost · scikit-learn · SHAP · Plotly · Streamlit · Git

## 🙏 Crédits

- Inspiration : dataset Kaggle [HydraXAI — Geospatial AI](https://www.kaggle.com/datasets/rushabhahire01/hydraxai-geospatial-ai)
- Données : Géorisques (GASPAR), Météo-France (SIM / SWI), IGN (RGE ALTI), geo.api.gouv.fr
- Fond de carte : © CARTO, © les contributeurs OpenStreetMap

## 👩‍💻 Autrice

**Asma Ammouri** : ingénieure géologue (plus de 13 ans d'expérience en risques naturels et SIG) reconvertie dans la data · [GitHub](https://github.com/Asma-Iam)
