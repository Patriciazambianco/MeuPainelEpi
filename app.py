import streamlit as st
import pandas as pd
import plotly.express as px

# URL do arquivo Excel no GitHub (raw)
URL_GITHUB = ""https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

@st.cache_data
def carregar_dados():
    df = pd.read_excel(URL_GITHUB, engine="openpyxl")
    return df

def filtrar_por_tecnico(df):
    # Converter para datetime e tratar erros
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

    # Para cada técnico, manter apenas a última inspeção (se existir)
    df_ultimo = df.sort_values("DATA_INSPECAO").groupby("TÉCNICO").last().reset_index()

    # Trazer também técnicos sem inspeção (pendentes)
    tecnicos_com_inspecao = set(df_ultimo["TÉCNICO"])
    tecnicos_sem_inspecao = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)][["TÉCNICO"]].drop_duplicates()

    # Unir pendentes (sem inspeção) com os que têm última inspeção
    df_final = pd.concat([df_ultimo, tecnicos_sem_inspecao], ignore_index=True, sort=False)

    return df_final

def calcular_percentuais(df):
    total = len(df)
    ok = df["DATA_INSPECAO"].notna().sum()
    pendente = df["DATA_INSPECAO"].isna().sum()

    perc_ok = round((ok / total) * 100, 2) if total else 0
    perc_pendente = round((pendente / total) * 100, 2) if total else 0

    return perc_ok, perc_pendente

def grafico_pizza_por_col(df, coluna, titulo):
    resumo = df.groupby(coluna).agg(
        OK = pd.NamedAgg(column="DATA_INSPECAO", aggfunc=lambda x: x.notna().sum()),
        Pendente = pd.NamedAgg(column="DATA_INSPECAO", aggfunc=lambda x: x.isna().sum())
    ).reset_index()

    dados_melt = resumo.melt(id_vars=coluna, value_vars=["OK", "Pendente"], var_name="Status", value_name="Quantidade")

    fig = px.pie(
        dados_melt,
        names="Status",
        values="Quantidade",
        color="Status",
        color_discrete_map={"OK": "green", "Pendente": "red"},
        title=titulo,
        facet_col=coluna,
        facet_col_wrap=3
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(margin=dict(t=50,b=0,l=0,r=0), legend_title_text='Status')
    return fig

# --- Início do app ---

st.set_page_config(page_title="Dashboard de Inspeções EPI", layout="wide")

st.title("🔍 Dashboard de Inspeções EPI")

# Botão para baixar apenas pendentes
df_raw = carregar_dados()
df_filtrado = filtrar_por_tecnico(df_raw)

pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]
excel_bytes = pendentes.to_excel(index=False, engine="openpyxl")
st.download_button(
    label="📥 Baixar Excel com Pendências",
    data=excel_bytes,
    file_name="pendencias_epi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download-pendentes",
)

# Mostrar métricas gerais
perc_ok, perc_pendente = calcular_percentuais(df_filtrado)

col1, col2 = st.columns(2)
col1.metric("✅ % Inspeções OK", f"{perc_ok:.2f}%")
col2.metric("⚠️ % Pendentes", f"{perc_pendente:.2f}%")

# Gráfico por gerente
st.plotly_chart(grafico_pizza_por_col(df_filtrado, "GERENTE", "Status por Gerente"), use_container_width=True)

# Gráfico por coordenador
st.plotly_chart(grafico_pizza_por_col(df_filtrado, "COORDENADOR", "Status por Coordenador"), use_container_width=True)
