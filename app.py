import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- Login automático ---
NOME_USUARIO = "Pati"
st.markdown(f"👋 Bem-vindo(a), **{NOME_USUARIO}**!")

# --- Função para carregar dados direto do GitHub ---
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Função para filtrar última inspeção por TÉCNICO ---
def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas_por_tecnico = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)
    return resultado

# --- Função para download do Excel tratado ---
def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx" style="font-size:18px; color:#fff; background-color:#007acc; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Baixar Excel Tratado</a>'
    return href

# --- CSS dos KPIs ---
kpi_css = """
<style>
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
</style>
"""

# --- Título ---
st.title("🦺 Painel de Inspeções EPI")

# --- Dados ---
df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# --- Filtros ---
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
pending = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pending
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1)

# --- Mostra KPIs ---
st.markdown(kpi_css, unsafe_allow_html=True)
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

# --- Gráfico Pizza ---
fig = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pending],
    title="Status das Inspeções",
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
)
st.plotly_chart(fig, use_container_width=True)

# --- Gráfico por Coordenador ---
status_por_coord = (
    df_filtrado
    .groupby(["COORDENADOR", df_filtrado["DATA_INSPECAO"].notna()])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "OK", False: "Pendentes"})
    .reset_index()
)
status_por_coord["Total"] = status_por_coord["OK"] + status_por_coord["Pendentes"]
status_por_coord["% OK"] = (status_por_coord["OK"] / status_por_coord["Total"]) * 100

if not status_por_coord.empty:
    fig2 = px.bar(
        status_por_coord,
        x="COORDENADOR",
        y="% OK",
        title="% Inspeções OK por Coordenador",
        labels={"% OK": "% Inspeções OK", "COORDENADOR": "Coordenador"},
        text=status_por_coord["% OK"].apply(lambda x: f"{x:.1f}%"),
        color="% OK",
        color_continuous_scale=px.colors.sequential.Mint
    )
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Nenhum dado disponível para o gráfico de coordenadores.")

# --- Tabela ---
st.markdown("### Dados Tratados")
st.dataframe(df_filtrado, use_container_width=True)
st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)
