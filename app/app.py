from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data" / "predictions_v3.parquet"

# Nom lisible et unité de chaque variable du modèle
VARIABLES = {
    "swi_moyen": ("SWI moyen", "{:.2f}"),
    "swi_max": ("SWI maximal", "{:.2f}"),
    "swi_p90": ("SWI 90e percentile", "{:.2f}"),
    "part_mois_sature": ("Part des mois saturés", "{:.0%}"),
    "altitude": ("Altitude", "{:.0f} m"),
    "denivele_local": ("Dénivelé local", "{:.0f} m"),
    "pente_max_pct": ("Pente max", "{:.1f} %"),
    "position_relative": ("Position relative", "{:+.0f} m"),
    "pluie_max_jour_moy": ("Pluie max d'un jour (moyenne annuelle)", "{:.0f} mm"),
    "pluie_max_jour_abs": ("Record de pluie en un jour", "{:.0f} mm"),
    "nb_jours_50mm_an": ("Jours ≥ 50 mm par an", "{:.2f}"),
    "cumul_annuel_moy": ("Cumul annuel moyen", "{:.0f} mm"),
}

st.set_page_config(page_title="HydraXAI France", layout="wide")
st.title("HydraXAI France : risque inondation par commune")
st.caption("Modèle XGBoost (humidité des sols, relief IGN, pluies extrêmes), validation spatiale par département. "
           "Projet portfolio : ne remplace pas les documents officiels (Géorisques, PPRI).")


@st.cache_data
def charger():
    df = pd.read_parquet(DATA)
    # Nom + département pour distinguer les homonymes
    df["libelle"] = df["nom"] + " (" + df["codeDepartement"] + ")"
    df["rang"] = df["proba_risque"].rank(pct=True)
    return df


@st.cache_data
def carte(df):
    fig = px.scatter_map(
        df, lat="lat", lon="lon", color="proba_risque",
        color_continuous_scale="YlOrRd", range_color=(0, 1),
        hover_name="libelle",
        hover_data={"proba_risque": ":.0%", "nb_arretes_inond": True, "lat": False, "lon": False},
        labels={"proba_risque": "Probabilité", "nb_arretes_inond": "Arrêtés"},
        zoom=4.5, center={"lat": 46.6, "lon": 2.5}, height=650,
    )
    fig.update_traces(marker={"size": 3})
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
    return fig


def graphique_shap(ligne):
    contrib = pd.DataFrame({
        "variable": [f"{nom} = {fmt.format(ligne[v])}" for v, (nom, fmt) in VARIABLES.items()],
        "shap": [ligne[f"shap_{v}"] for v in VARIABLES],
    })
    contrib = contrib.reindex(contrib["shap"].abs().sort_values().index)
    fig = go.Figure(go.Bar(
        x=contrib["shap"], y=contrib["variable"], orientation="h",
        marker_color=["#d7301f" if s > 0 else "#2b8cbe" for s in contrib["shap"]],
    ))
    fig.update_layout(height=420, margin={"l": 0, "r": 0, "t": 10, "b": 0},
                      xaxis_title="Contribution SHAP (log-odds)")
    return fig


df = charger()

commune = st.selectbox("Choisir une commune", sorted(df["libelle"].unique()))
ligne = df[df["libelle"] == commune].iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("Probabilité d'exposition forte", f"{ligne['proba_risque']:.0%}",
            help="Probabilité d'avoir 6 arrêtés CatNat inondation ou plus. "
                 "Calibrée : sur 100 communes à 30 %, environ 30 sont réellement dans ce cas.")
col2.metric("Rang parmi les communes", f"{ligne['rang']:.0%}",
            help="Part des communes de métropole dont la probabilité est plus faible.")
col3.metric("Arrêtés CatNat inondation (réels)", int(ligne["nb_arretes_inond"]))

gauche, droite = st.columns([3, 2])
with gauche:
    fig = carte(df)
    fig.add_trace(go.Scattermap(
        lat=[ligne["lat"]], lon=[ligne["lon"]], mode="markers",
        marker={"size": 16, "color": "#08519c"}, name=ligne["nom"],
        hoverinfo="text", text=[ligne["libelle"]], showlegend=False,
    ))
    st.plotly_chart(fig)
with droite:
    st.subheader("Pourquoi cette probabilité ?")
    st.caption("Rouge : la variable augmente le risque par rapport à une commune moyenne. Bleu : elle le diminue.")
    st.plotly_chart(graphique_shap(ligne))

st.caption("Probabilités et explications **hors échantillon** : chaque commune est prédite et expliquée "
           "par un modèle qui n'a vu aucune commune de son département. "
           "SHAP explique le modèle, pas une causalité physique.")
