import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="HydraXAI France", layout="wide")
st.title("HydraXAI France : risque inondation par commune")
st.caption("Modèle XGBoost (SWI + relief IGN), validation spatiale par département. "
           "Projet portfolio : ne remplace pas les documents officiels (Géorisques, PPRI).")

@st.cache_data
def charger():
    df = pd.read_parquet("data/predictions_communes.parquet")
    # Retirer les communes sans nom ni coordonnées (anciennes communes fusionnées)
    df = df.dropna(subset=["nom", "lat", "lon"])
    # Nom + département pour distinguer les homonymes
    df["libelle"] = df["nom"] + " (" + df["codeDepartement"] + ")"
    return df

df = charger()

# Recherche d'une commune
commune = st.selectbox("Choisir une commune", sorted(df["libelle"].unique()))
ligne = df[df["libelle"] == commune].iloc[0]

col1, col2 = st.columns(2)
col1.metric("Probabilité d'exposition forte", f"{ligne['proba_risque']:.0%}")
col2.metric("Arrêtés CatNat inondation (réels)", int(ligne["nb_arretes_inond"]))

# Carte de France
fig = px.scatter_map(
    df, lat="lat", lon="lon", color="proba_risque",
    color_continuous_scale="YlOrRd", range_color=(0, 1),
    hover_name="nom", zoom=4.5, center={"lat": 46.6, "lon": 2.5}, height=650,
)
fig.update_traces(marker={"size": 3})
st.plotly_chart(fig, use_container_width=True)
