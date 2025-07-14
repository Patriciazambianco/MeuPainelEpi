import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Gráfico de Inspeções", layout="wide")
st.title("📊 Percentual de Inspeções por Coordenador")

# Carregar dados do Excel online
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    return pd.read_excel(url, engine="openpyxl")

# Filtrar somente a última inspeção por técnico
def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates("TÉCNICO", keep="last")
    tecnicos_com_inspecao = ultimas["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates("TÉCNICO")
    return pd.concat([ultimas, sem_data], ignore_index=True)

# Carrega e trata os dados
df_raw = carregar_dados()
df = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# Agrupa por coordenador e calcula totais
df_status = df.groupby("COORDENADOR").apply(lambda x: pd.Series({
    "OK": x["DATA_INSPECAO"].notna().sum(),
    "Pendentes": x["DATA_INSPECAO"].isna().sum(),
    "Total": len(x)
})).reset_index()

# Calcula os percentuais
df_status["% OK"] = (df_status["OK"] / df_status["Total"] * 100).round(1)
df_status["% Pendentes"] = (df_status["Pendentes"] / df_status["Total"] * 100).round(1)

# Prepara para gráfico
df_melt = df_status.melt(
    id_vars="COORDENADOR",
    value_vars=["% OK", "% Pendentes"],
    var_name="Status",
    value_name="Percentual"
)

# Cores personalizadas
cores = {
    "% OK": "#27ae60",        # Verde
    "% Pendentes": "#f39c12"  # Laranja
}

# Gráfico empilhado por coordenador
fig = px.bar(
    df_melt,
    x="COORDENADOR",
    y="Percentual",
    color="Status",
    color_discrete_map=cores,
    text="Percentual",
    title="📊 Inspeções Realizadas e Pendentes por Coordenador",
    labels={"COORDENADOR": "Coordenador", "Percentual": "%"}
)
fig.update_layout(barmode="stack", xaxis_tickangle=-45, yaxis_range=[0, 100])
fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")

# Exibe o gráfico
st.plotly_chart(fig, use_container_width=True)
