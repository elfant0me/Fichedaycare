import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Fiche d'assiduité",
    layout="wide"
)

st.title("Fiche d'assiduité")

# Lire le fichier HTML
with open("fiche_assiduite.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Afficher le HTML
components.html(html_content, height=900, scrolling=True)
