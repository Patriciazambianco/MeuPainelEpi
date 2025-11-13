import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# 🎨 CONFIGURAÇÃO GERAL
st.set_page_config(page_title="Check List  EPI - Técnicos OK/Pendentes", layout="wide")

# CSS personalizado 💅
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #f8fbff, #f3e5f5);
    }
    h1 {
        text-align: center;
        color: #1b5e20;
        font-weight: 800;
        font-size: 2.2rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 13px;
        border-radius: 13px;
        color: white;
        font-weight: bold;
        text-align: center;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: scale(1.05);
    }
    .ok-card {background: linear-gradient(135deg, #2ecc71, #27ae60);}
    .pendente-card {background: linear-gradient(135deg, #e74c3c, #c0392b);}
    .percent-ok-card {background: linear-gradient(135deg, #3498db, #2980b9);}
    .percent-pend-card {background: linear-gradient(135deg, #f1c40f, #f39c12);}
    .stDownloadButton button {
        background-color: #1b5e20;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        box-shadow: 0px 3px 6px rgba(0,0,0,0.2);
    }
    .stDownloadButton button:hover {
        background-color: #43a047;
        transform: scale(1.03);
        transition: 0.2s;
    }
    </style>
""", unsafe_allow_html=True)

# 🧠 TÍTULO
st.title("🦺 Check List EPI - Técnicos OK e Pendentes")

# 🚀 FUNÇÃO DE CARGA
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
    return df

# 🔗 URL
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)

# 🎯 FILTROS
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())
produtos = ["Todos"] + sorted(df["PRODUTO_SIMILAR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("👩‍💼 Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("🧑‍🏭 Coordenador", coordenadores)
produto_sel = st.sidebar.selectbox("🧰 Produto", produtos)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]
if produto_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["PRODUTO_SIMILAR"] == produto_sel]

# 📋 VISUALIZAÇÃO GERAL
st.markdown("### 📋 Dados Filtrados")
st.dataframe(df_filtrado)

# 📦 FUNÇÃO DE DOWNLOAD
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button(
    "📥 Baixar Dados Filtrados (Excel)",
    data=to_excel(df_filtrado),
    file_name="dados_filtrados_epi.xlsx"
)
