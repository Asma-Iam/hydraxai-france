# HydraXAI France 🌊 — Cartographie explicable du risque inondation par commune

**👉 Démo en ligne : [hydraxai-france.streamlit.app](https://hydraxai-france.streamlit.app)**

Modèle de machine learning géospatial qui estime, pour chaque commune de France métropolitaine, la probabilité d'une **exposition forte aux inondations**, et **explique** ses prédictions avec SHAP.

> ⚠️ Projet portfolio à visée pédagogique. Il ne remplace pas les documents officiels (Géorisques, PPRI, DICRIM).

---

## 🎯 Problématique

Les arrêtés de catastrophe naturelle (CatNat) « inondation » montrent que certaines communes sont reconnues sinistrées bien plus souvent que d'autres.
**Peut-on expliquer ces différences à partir du terrain (relief, humidité des sols) ? Et quelles variables comptent le plus ?**

## 📊 Données

| Donnée | Source | Traitement |
|---|---|---|
| Arrêtés CatNat inondation | Base GASPAR (Géorisques), via BigQuery | Libellés « inondations et/ou coulées de boue » et « inondations remontée nappe » |
| Humidité des sols (SWI) | Météo-France, grille SIM (8 981 points, maille 8 km), 1982 → aujourd'hui | Plus proche voisin depuis le centre de chaque commune (Lambert-93, 10 km max) → 99 % des communes couvertes |
| Relief | IGN, RGE ALTI (API altimétrique de la Géoplateforme) | 5 points par commune (centre + 4 points à 1 km) → 172 380 altitudes |
| Centres des communes | API Découpage administratif (geo.api.gouv.fr) | Coordonnées WGS84 |

**Périmètre :** 34 455 communes de France métropolitaine.

## 🧭 Méthode

**1. Cible.** La médiane est de 3 arrêtés par commune et le 75ᵉ percentile de 5.
→ `risque_fort = 1` si la commune compte **6 arrêtés ou plus** (23,5 % des communes).

**2. Variables (8)**
- SWI : `swi_moyen`, `swi_max`, `swi_p90`, `part_mois_sature` (part des mois avec SWI ≥ 1)
- Relief : `altitude`, `denivele_local`, `pente_max_pct`, `position_relative` (indice proche du TPI : centre − moyenne des voisins)

Les coordonnées ne sont **pas** utilisées comme variables : le modèle doit apprendre du terrain, pas de la position sur la carte.

**3. Modèle.** XGBoost (300 arbres, profondeur 4), avec `scale_pos_weight` pour compenser le déséquilibre 76 % / 24 %.

**4. Validation spatiale.** `GroupKFold` par département : le modèle est toujours testé sur des départements qu'il n'a jamais vus.

## 📈 Résultats

| Métrique | Validation aléatoire | **Validation spatiale** | Hasard |
|---|---|---|---|
| ROC-AUC | 0,775 | **0,717** | 0,5 |
| PR-AUC | 0,562 | **0,462** | 0,235 |
| Recall (classe 1) | 0,646 | **0,580** | – |

- La validation aléatoire **surestime** la performance : les communes voisines se ressemblent (autocorrélation spatiale).
- En validation spatiale, la PR-AUC est **presque le double** du hasard.

## 🔍 Explicabilité (SHAP)

- **Altitude** : les communes basses sont plus exposées.
- **SWI** : un SWI maximal élevé *et* un SWI moyen faible augmentent le risque. Ce profil (sol souvent sec, mais saturé ponctuellement) évoque des **épisodes de pluies intenses**, une hypothèse à vérifier dans la v2.
- **Dénivelé local** : un relief marqué augmente le risque (la cible inclut les coulées de boue).
- `pente_max_pct` et `position_relative` apportent peu.

La carte des probabilités fait ressortir le pourtour méditerranéen, le Sud-Ouest et les grands axes de vallées.

## ⚠️ Limites

- **La cible mesure les inondations *reconnues*** : un arrêté CatNat n'existe que si la commune en fait la demande.
- **Les erreurs sont regroupées par région** (au seuil de 0,5 : 69,7 % correct, 20,2 % de fausses alertes, 10,1 % de risques manqués), ce qui indique des informations régionales manquantes.
- Le centre de la commune ne représente pas toute sa surface.
- Les variables de SWI sont corrélées entre elles : leurs contributions SHAP se lisent ensemble.
- SHAP explique le modèle, pas une causalité physique.

## 🚀 Suite (v2)

- Ajouter les **pluies extrêmes** (cumuls journaliers maximums, nombre de jours à plus de 50 mm)
- Ajouter la **distance au cours d'eau** et la taille du bassin versant
- Tester une régression sur le **nombre** d'arrêtés

## 🗂️ Structure du dépôt

```
hydraxai-france/
├── app/
│   ├── app.py               # application Streamlit
│   └── requirements.txt     # dépendances de l'app
├── data/                    # tables préparées (parquet)
├── notebooks/
│   └── 01_exploration_catnat.ipynb   # préparation des données, modèle, SHAP, cartes
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
