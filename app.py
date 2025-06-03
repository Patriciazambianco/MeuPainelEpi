import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- CSS para fundo, KPIs e botão piscando ---
custom_css = """
<style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }

    .kpi-container {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .kpi-box {
        background-color: #007acc;
        color: white;
        border-radius: 10px;
        padding: 20px 30px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 6px rgb(0 0 0 / 0.1);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .kpi-box.pending {
        background-color: #f39c12;
    }

    .kpi-box.percent {
        background-color: #27ae60;
    }

    .kpi-title {
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }

    /* Botão piscando */
    .blinking-button {
        font-size: 16px;
        color: white !important;
        background-color: #e74c3c;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        animation: blink 1s infinite;
        font-weight: bold;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .download-top {
        display: flex;
        justify-content: flex-end;
        margin-top: -40px;
        margin-bottom: 20px;
    }

    /* Ajusta texto das tabelas */
    .stDataFrame div.row_widget.stDataFrameWidget div.cell, 
    .stDataFrame div.row_widget.stDataFrameWidget div.cell > div {
        color: black !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Função para carregar dados direto do GitHub ---
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Função para tratar por técnico (última inspeção ou pendente) ---
def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    tecnicos_com_inspecao = ultimas["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates(subset=["TÉCNICO"])
    return pd.concat([ultimas, sem_data], ignore_index=True)

# --- Função para gerar botão de download com pendências ---
def gerar_download_pendencias_excel(df):
    pendencias = df[df["DATA_INSPECAO"].isna()]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pendencias.to_excel(writer, index=False, sheet_name="Pendencias")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'''
    <div class="download-top">
        <a href="data:application/octet-stream;base64,{b64}" 
           download="pendencias_inspecao.xlsx" 
           class="blinking-button">📥 Baixar Pendências (Excel)</a>
    </div>
    '''
    return href

# --- INÍCIO DO APP ---
st.title("🦺 Painel de Inspeções EPI")
df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# Botão de download no topo
st.markdown(gerar_download_pendencias_excel(df_tratado), unsafe_allow_html=True)

# Filtros
col1, col2 = st.columns(2)
gerentes = df_tratado["GERENTE"].dropna().unique()
coordenadores = df_tratado["COORDENADOR"].dropna().unique()

with col1:
    gerente_sel = st.multiselect("Filtrar por Gerente", sorted(gerentes))
with col2:
    coordenador_sel = st.multiselect("Filtrar por Coordenador", sorted(coordenadores))

df_filtrado = df_tratado.copy()
if gerente_sel:
    df_filtrado = df_filtrado[df_filtrado["GERENTE"].isin(gerente_sel)]
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

# KPIs
total = len(df_filtrado)
pending = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pending
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1)

# KPIs visuais
kpis_html = f"""
<div class="kpi-container">
    <div class="kpi-box percent">
        <div class="kpi-title">Inspeções OK</div>
        <div class="kpi-value">{ok}</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">Pendentes</div>
        <div class="kpi-value">{pending}</div>
    </div>
    <div class="kpi-box percent">
        <div class="kpi-title">% OK</div>
        <div class="kpi-value">{pct_ok}%</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">% Pendentes</div>
        <div class="kpi-value">{pct_pendente}%</div>
    </div>
</div>
"""
st.markdown(kpis_html, unsafe_allow_html=True)

# Gráfico
fig = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pending],
    title="Status das Inspeções",
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
)
st.plotly_chart(fig, use_container_width=True)

# Tabela
st.markdown("### 🔍 Dados Tratados")
st.dataframe(df_filtrado, use_container_width=True)
