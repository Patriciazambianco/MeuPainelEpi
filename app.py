import streamlit as st
import pandas as pd
import plotly.express as px
import io
import base64

st.set_page_config(page_title="Inspeções EPI", layout="wide")

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas_por_tecnico = (
        com_data
        .sort_values("DATA_INSPECAO")
        .drop_duplicates(subset=["TÉCNICO"], keep="last")
    )
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)
    return resultado

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="pendentes_inspecoes.xlsx" style="animation: piscar 1.5s infinite; font-size:18px; color:#fff; background-color:#e74c3c; padding:10px 15px; border-radius:5px; text-decoration:none; font-weight:700; display:inline-block; margin-bottom:20px;">📥 Baixar Pendentes</a>'
    return href

st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# FILTRO GERENTE
gerentes = df_tratado["GERENTE"].dropna().unique()
gerente_sel = st.multiselect("Filtrar por Gerente", sorted(gerentes))

# FILTRO COORDENADOR depende do gerente selecionado
if gerente_sel:
    df_gerente = df_tratado[df_tratado["GERENTE"].isin(gerente_sel)]
    coord_filtrados = df_gerente["COORDENADOR"].dropna().unique()
else:
    df_gerente = df_tratado.copy()
    coord_filtrados = df_tratado["COORDENADOR"].dropna().unique()

coordenador_sel = st.multiselect("Filtrar por Coordenador", sorted(coord_filtrados))

# Aplica filtros combinados no df
df_filtrado = df_gerente.copy()
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

# Pendentes só do filtro completo
df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]

# KPI percentual geral por GERENTE (independente do coordenador)
total_gerente = len(df_gerente)
pending_gerente = df_gerente["DATA_INSPECAO"].isna().sum()
ok_gerente = total_gerente - pending_gerente
pct_ok_gerente = round(ok_gerente / total_gerente * 100, 1) if total_gerente > 0 else 0
pct_pendente_gerente = round(100 - pct_ok_gerente, 1)

st.markdown(f"""
<style>
    .kpi-gerente {{
        background-color: #27ae60;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.3rem;
        width: fit-content;
        margin-bottom: 15px;
    }}
</style>
<div class="kpi-gerente">
    Percentual OK Geral do(s) Gerente(s) Selecionado(s): {pct_ok_gerente}%
</div>
""", unsafe_allow_html=True)

# Download pendentes piscando
st.markdown(gerar_download_excel(df_pendentes), unsafe_allow_html=True)

# Gráfico de barras OK/Pendentes por coordenador (com base no filtro)
df_status_coord = df_filtrado.groupby(["COORDENADOR", "DATA_INSPECAO"]).size().unstack(fill_value=0)
df_status_coord["OK"] = df_status_coord[df_status_coord.columns.difference([pd.NaT])].sum(axis=1) if pd.NaT in df_status_coord.columns else 0
df_status_coord["Pendentes"] = df_status_coord.get(pd.NaT, 0)

# Ajusta para garantir colunas OK e Pendentes
if "OK" not in df_status_coord.columns:
    df_status_coord["OK"] = 0
if "Pendentes" not in df_status_coord.columns:
    df_status_coord["Pendentes"] = 0

df_plot = df_status_coord[["OK", "Pendentes"]].reset_index()

fig = px.bar(
    df_plot.melt(id_vars="COORDENADOR", value_vars=["OK", "Pendentes"]),
    x="COORDENADOR",
    y="value",
    color="variable",
    color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"},
    labels={"value": "Quantidade", "variable": "Status"},
    title="Status das Inspeções por Coordenador",
    text="value"
)

fig.update_traces(textposition="outside")
fig.update_layout(yaxis_title="Quantidade", xaxis_title="Coordenador", uniformtext_minsize=8, uniformtext_mode='hide')

st.plotly_chart(fig, use_container_width=True)

# Mostrar tabela dos pendentes
st.markdown("### Dados Pendentes")
st.dataframe(df_pendentes, use_container_width=True)
