import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px
import requests

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- Estilo CSS ---
st.markdown("""
    <style>
    body {
        background-color: #f0f2f6;
    }
    .css-18e3th9 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
    }
    .download-btn {
        font-weight: bold;
        color: white;
        background-color: #ff4b4b;
        padding: 10px;
        border-radius: 8px;
        text-decoration: none;
        animation: blink 1s infinite;
    }
    @keyframes blink {
      0% {opacity: 1;}
      50% {opacity: 0.5;}
      100% {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

# --- Função para carregar dados direto do GitHub ---
@st.cache_data

def carregar_dados():
    url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%83O%20EPI.xlsx"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Erro ao carregar o arquivo do GitHub.")
        return pd.DataFrame()
    file_bytes = io.BytesIO(response.content)
    df = pd.read_excel(file_bytes, engine="openpyxl")
    # Padroniza nomes das colunas
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_").str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    return df

# --- Função para filtrar última inspeção por TÉCNICO ---
def filtrar_por_tecnico(df):
    df["DATA_DA_INSPECAO"] = pd.to_datetime(df["DATA_DA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_DA_INSPECAO"].notna()]
    sem_data = df[df["DATA_DA_INSPECAO"].isna()]
    ultimas = com_data.sort_values("DATA_DA_INSPECAO").drop_duplicates(subset=["TECNICO"], keep="last")
    sem_data = sem_data[~sem_data["TECNICO"].isin(ultimas["TECNICO"])]
    return pd.concat([ultimas, sem_data], ignore_index=True)

# --- Função para permitir download apenas das pendências ---
def gerar_download_pendencias(df):
    pendentes = df[df["DATA_DA_INSPECAO"].isna()]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pendentes.to_excel(writer, index=False, sheet_name="Pendencias")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a class="download-btn" href="data:application/octet-stream;base64,{b64}" download="pendencias.xlsx">📥 Baixar Pendências</a>'
    return href

# --- Início do app ---
st.title("📋 Painel de Inspeções EPI")

# Carrega e trata os dados
df_raw = carregar_dados()
df_tratado = filtrar_por_tecnico(df_raw)

# Filtros
col1, col2 = st.columns(2)
gerentes = df_tratado["GERENTE"].dropna().unique()
coordenadores = df_tratado["COORDENADOR"].dropna().unique()

with col1:
    gerente_sel = st.multiselect("👔 Filtrar por Gerente", sorted(gerentes))
with col2:
    coordenador_sel = st.multiselect("🧭 Filtrar por Coordenador", sorted(coordenadores))

df_filtrado = df_tratado.copy()
if gerente_sel:
    df_filtrado = df_filtrado[df_filtrado["GERENTE"].isin(gerente_sel)]
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

# KPIs
total = len(df_filtrado)
pendentes = df_filtrado["DATA_DA_INSPECAO"].isna().sum()
ok = total - pendentes
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1)

st.markdown("""
### 🌟 Indicadores Gerais
""")
col3, col4, col5 = st.columns(3)
col3.metric("✅ Inspeções OK", ok)
col4.metric("❌ Pendentes", pendentes)
col5.metric("📊 % OK / Pendentes", f"{pct_ok}% / {pct_pendente}%")

# Botão de download
st.markdown(gerar_download_pendencias(df_filtrado), unsafe_allow_html=True)

# Gráficos por gerente e coordenador
if not df_filtrado.empty:
    with st.expander("📈 Gráficos por Gerente e Coordenador", expanded=True):
        # Gráfico por GERENTE
        fig1 = px.pie(df_filtrado, names="GERENTE", title="Distribuição por Gerente", hole=0.4)
        # Gráfico por COORDENADOR
        fig2 = px.pie(df_filtrado, names="COORDENADOR", title="Distribuição por Coordenador", hole=0.4)
        col1, col2 = st.columns(2)
        col1.plotly_chart(fig1, use_container_width=True)
        col2.plotly_chart(fig2, use_container_width=True)

# Tabela com os dados tratados
st.markdown("### 🧾 Dados Tratados")
st.dataframe(df_filtrado, use_container_width=True)
