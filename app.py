import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Painel de Inspeções EPI", layout="wide")

# --- Função para carregar dados direto do GitHub ---
@st.cache_data

def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Função para filtrar última inspeção por TÉCNICO + PRODUTO ---
def filtrar_ultimas_inspecoes(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

    # separa os com e sem inspeção
    com_data = df[df["DATA_INSPECAO"].notna()]
    sem_data = df[df["DATA_INSPECAO"].isna()]

    # pega apenas a última por TÉCNICO + PRODUTO
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO", "PRODUTO_SIMILAR"], keep="last")

    # filtra os sem inspeção que ainda não existem em ultimas
    sem_data = sem_data.merge(ultimas[["TÉCNICO", "PRODUTO_SIMILAR"]], on=["TÉCNICO", "PRODUTO_SIMILAR"], how="left", indicator=True)
    apenas_sem = sem_data[sem_data['_merge'] == 'left_only'].drop(columns=['_merge'])

    # concatena o resultado final
    resultado = pd.concat([ultimas, apenas_sem], ignore_index=True)
    return resultado

# --- Função para permitir download do Excel tratado ---
def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx">📥 Baixar Excel Tratado</a>'
    return href

# --- Início do app ---
st.title("Painel de Inspeções EPI")

# Carrega e trata os dados
df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes(df_raw)

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
pct_pendente = 100 - pct_ok

st.markdown("### Indicadores")
st.metric("Inspeções OK", ok)
st.metric("Pendentes", pending)
st.metric("% OK", f"{pct_ok}%")

# Gráfico pizza
fig = px.pie(names=["OK", "Pendente"], values=[ok, pending], title="Status das Inspeções")
st.plotly_chart(fig, use_container_width=True)

# Tabela e download
st.markdown("### Dados Tratados")
st.dataframe(df_filtrado, use_container_width=True)

st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)
