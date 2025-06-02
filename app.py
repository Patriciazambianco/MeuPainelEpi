import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

@st.cache_data
def carregar_dados_github(url):
    df = pd.read_excel(url)
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    # Ajusta a data 2001-01-01 para NaT (considera como nunca inspecionado)
    df.loc[df['DATA_INSPECAO'] == pd.Timestamp('2001-01-01'), 'DATA_INSPECAO'] = pd.NaT
    return df

def gerar_ultima_inspecao(df):
    # Pega só os registros com data de inspeção
    df_inspec = df[df['DATA_INSPECAO'].notnull()].copy()
    # Ordena do mais recente para o mais antigo
    df_inspec.sort_values(by=['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], ascending=[True, True, False], inplace=True)
    # Mantém só a última inspeção por técnico + produto (drop duplicados mantendo o mais recente)
    df_ult = df_inspec.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], keep='first')
    return df_ult

def gerar_nunca_inspecionados(df):
    # Registros que não tem data de inspeção (NaT)
    return df[df['DATA_INSPECAO'].isnull()]

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for nome, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=nome, index=False)
    output.seek(0)
    return output

# URL RAW do seu arquivo no GitHub
url_github = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

df = carregar_dados_github(url_github)

colunas_necessarias = ['DATA_INSPECAO', 'IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'GERENTE', 'COORDENADOR']
if not all(col in df.columns for col in colunas_necessarias):
    st.error("Arquivo enviado não possui as colunas necessárias.")
    st.stop()

# Filtragem para dropdown
gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique())
coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique())

gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['GERENTE'] == gerente_selecionado]
if coordenador_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['COORDENADOR'] == coordenador_selecionado]

ultimas = gerar_ultima_inspecao(df_filtrado)
nunca = gerar_nunca_inspecionados(df_filtrado)

total_registros = len(df_filtrado)
total_inspecionados = len(ultimas)
total_pendentes = len(nunca)
pct_inspecionados = (total_inspecionados / total_registros * 100) if total_registros else 0
pct_pendentes = (total_pendentes / total_registros * 100) if total_registros else 0

# Cards
col1, col2, col3 = st.columns(3)
col1.metric("Total Registros", total_registros)
col2.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
col3.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

# Gráfico pizza - Inspecionados x Pendentes
fig = px.pie(
    names=["Inspecionados", "Pendentes"],
    values=[total_inspecionados, total_pendentes],
    color_discrete_sequence=["#4CAF50", "#FF6F61"],
    title="📊 Distribuição de Inspeções"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("✅ Última Inspeção por Técnico + Produto")
st.dataframe(ultimas)

st.subheader("⚠️ Técnicos que Nunca Foram Inspecionados")
st.dataframe(nunca)

output_excel = exportar_excel({'Ultima_Inspecao': ultimas, 'Nunca_Inspecionados': nunca})

st.download_button(
    label="⬇️ Baixar Excel com Resultados",
    data=output_excel,
    file_name="inspecoes_epi_resultado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
