import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas_por_tecnico = (
        com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    )
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    return pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)

# Load e preparar dados
df_raw = carregar_dados()
df = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# Criar flag SEM EPI
df["SEM EPI"] = df["SALDO SGM TÉCNICO"].apply(
    lambda x: 1 if isinstance(x, str) and "não tem no saldo" in x.lower() else 0
)

# Agrupar por coordenador e calcular os %s
df_status = df.groupby("COORDENADOR").apply(lambda x: pd.Series({
    "OK": x["DATA_INSPECAO"].notna().sum(),
    "Pendentes": x["DATA_INSPECAO"].isna().sum(),
    "Sem EPI": x["SEM EPI"].sum(),
    "Total": len(x)
})).reset_index()

df_status["% OK"] = (df_status["OK"] / df_status["Total"] * 100).round(1)
df_status["% Pendentes"] = (df_status["Pendentes"] / df_status["Total"] * 100).round(1)
df_status["% Sem EPI"] = (df_status["Sem EPI"] / df_status["Total"] * 100).round(1)

# Derreter os dados para gráfico empilhado
df_melt = df_status.melt(
    id_vars="COORDENADOR",
    value_vars=["% OK", "% Pendentes", "% Sem EPI"],
    var_name="Status",
    value_name="Percentual"
)

# Garantir nomes limpos
df_melt["Status"] = df_melt["Status"].str.strip()

# Cores
cores = {
    "% OK": "#27ae60",
    "% Pendentes": "#f39c12",
    "% Sem EPI": "#e74c3c"
}

# Gráfico
fig = px.bar(
    df_melt,
    x="COORDENADOR",
    y="Percentual",
    color="Status",
    color_discrete_map=cores,
    text="Percentual",
    title="📊 Inspeções e Técnicos sem EPI por Coordenador",
    labels={"COORDENADOR": "Coordenador", "Percentual": "%"}
)
fig.update_layout(barmode="stack", xaxis_tickangle=-45, yaxis_range=[0, 100])
fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")

st.plotly_chart(fig, use_container_width=True)
