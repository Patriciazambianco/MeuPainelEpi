import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

# Configuração inicial
st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- CSS para KPIs no topo ---
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

# Aplica o estilo
st.markdown(kpi_css, unsafe_allow_html=True)

# --- Carregamento de dados do GitHub ---
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Lógica de última inspeção por técnico ---
def filtrar_ultimas_inspecoes(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates("TÉCNICO", keep="last")
    sem_data = df[~df["TÉCNICO"].isin(ultimas["TÉCNICO"])].drop_duplicates("TÉCNICO")
    return pd.concat([ultimas, sem_data], ignore_index=True)

# --- Baixar Excel tratado ---
def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    b64 = base64.b64encode(output.getvalue()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx" style="font-size:18px; color:#fff; background-color:#007acc; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Baixar Excel Tratado</a>'
    return href

# --- Título do painel ---
st.title("🦺 Painel de Inspeções EPI")

# Simula login automático do usuário "pati"
st.success("👋 Olá, Pati! Você está logada automaticamente.")

# --- Carrega dados e trata ---
df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes(df_raw)

# --- Filtros: gerente e coordenador ---
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

# --- KPIs ---
total = len(df_filtrado)
pendentes = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pendentes
pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = 100 - pct_ok

kpis_html = f"""
<div class="kpi-container">
    <div class="kpi-box percent">
        <div class="kpi-title">Inspeções OK</div>
        <div class="kpi-value">{ok}</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">Pendentes</div>
        <div class="kpi-value">{pendentes}</div>
    </div>
    <div class="kpi-box percent">
        <div class="kpi-title">% OK</div>
        <div class="kpi-value">{pct_ok}%</div>
    </div>
    <div class="kpi-box pending">
        <div class="kpi-title">% Pendentes</div>
        <div class="kpi-value">{pct_pend}%</div>
    </div>
</div>
"""
st.markdown(kpis_html, unsafe_allow_html=True)

# --- Gráfico de pizza ---
fig1 = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pendentes],
    title="Status das Inspeções",
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
)
st.plotly_chart(fig1, use_container_width=True)

# --- Gráfico de barra por coordenador ---
status_coord = (
    df_filtrado
    .groupby(["COORDENADOR", df_filtrado["DATA_INSPECAO"].notna()])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "OK", False: "Pendentes"})
    .reset_index()
)

if not status_coord.empty:
    status_coord["Total"] = status_coord["OK"] + status_coord["Pendentes"]
    status_coord["% OK"] = (status_coord["OK"] / status_coord["Total"]) * 100

    fig2 = px.bar(
        status_coord,
        x="COORDENADOR",
        y="% OK",
        title="% Inspeções OK por Coordenador",
        text_auto=".1f",
        color="% OK",
        color_continuous_scale=px.colors.sequential.Mint
    )
    fig2.update_layout(xaxis_title="Coordenador", yaxis_title="% OK")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Sem dados suficientes para gerar o gráfico de coordenadores.")

# --- Tabela final + botão de download ---
st.markdown("### 📋 Tabela de Inspeções")
st.dataframe(df_filtrado, use_container_width=True)
st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)
