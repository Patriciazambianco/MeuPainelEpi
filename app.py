import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Painel de Inspeções EPI", layout="wide", initial_sidebar_state="collapsed")

# Login automático
USUARIO_LOGADO = "Pati"
st.success(f"🔓 Login automático como **{USUARIO_LOGADO}**")

# --- Função para carregar dados direto do GitHub ---
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Filtrar última inspeção por técnico (único) ---
def filtrar_ultimas_inspecoes(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates("TÉCNICO", keep="last")
    tecnicos_com_inspecao = ultimas["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates("TÉCNICO")
    return pd.concat([ultimas, sem_data], ignore_index=True)

# --- Download do Excel tratado ---
def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    b64 = base64.b64encode(output.getvalue()).decode()
    link = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx">📥 Baixar Excel</a>'
    return link

# --- CSS para os KPIs ---
kpi_css = """
<style>
.kpi-container {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}
.kpi-box {
    background-color: #007acc;
    color: white;
    border-radius: 10px;
    padding: 20px;
    flex: 1;
    text-align: center;
    font-family: 'Segoe UI', sans-serif;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
}
.kpi-box.pending { background-color: #f39c12; }
.kpi-box.percent { background-color: #27ae60; }
.kpi-title { font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: bold; }
.kpi-value { font-size: 2.5rem; font-weight: bold; }
</style>
"""

# --- Painel ---
st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes(df_raw)

# Filtros
col1, col2 = st.columns(2)
with col1:
    gerente_sel = st.multiselect("Filtrar por Gerente", sorted(df_tratado["GERENTE"].dropna().unique()))
with col2:
    coordenador_sel = st.multiselect("Filtrar por Coordenador", sorted(df_tratado["COORDENADOR"].dropna().unique()))

df_filt = df_tratado.copy()
if gerente_sel:
    df_filt = df_filt[df_filt["GERENTE"].isin(gerente_sel)]
if coordenador_sel:
    df_filt = df_filt[df_filt["COORDENADOR"].isin(coordenador_sel)]

# KPIs
total = len(df_filt)
pendentes = df_filt["DATA_INSPECAO"].isna().sum()
ok = total - pendentes
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pend = 100 - pct_ok

st.markdown(kpi_css, unsafe_allow_html=True)
kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-box percent"><div class="kpi-title">Inspeções OK</div><div class="kpi-value">{ok}</div></div>
    <div class="kpi-box pending"><div class="kpi-title">Pendentes</div><div class="kpi-value">{pendentes}</div></div>
    <div class="kpi-box percent"><div class="kpi-title">% OK</div><div class="kpi-value">{pct_ok}%</div></div>
    <div class="kpi-box pending"><div class="kpi-title">% Pendentes</div><div class="kpi-value">{pct_pend}%</div></div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# Gráfico Pizza
fig1 = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pendentes],
    title="Status das Inspeções",
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
)
st.plotly_chart(fig1, use_container_width=True)

# Gráfico por Coordenador
df_bar = (
    df_filt.groupby(["COORDENADOR", df_filt["DATA_INSPECAO"].notna()])
    .size().unstack(fill_value=0)
    .rename(columns={True: "OK", False: "Pendentes"}).reset_index()
)
df_bar["Total"] = df_bar["OK"] + df_bar["Pendentes"]
df_bar["% OK"] = (df_bar["OK"] / df_bar["Total"]) * 100

if not df_bar.empty:
    fig2 = px.bar(
        df_bar, x="COORDENADOR", y="% OK", color="% OK",
        text=df_bar["% OK"].apply(lambda x: f"{x:.1f}%"),
        title="% Inspeções OK por Coordenador",
        color_continuous_scale="Mint"
    )
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)

# Tabela
st.markdown("### 📄 Dados Tratados")
st.dataframe(df_filt, use_container_width=True)

# Download
st.markdown(gerar_download_excel(df_filt), unsafe_allow_html=True)
