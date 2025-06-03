import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO

@st.cache_data
url_github = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados_github(url_github)

    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df.loc[df['DATA_INSPECAO'] == pd.Timestamp('2001-01-01'), 'DATA_INSPECAO'] = pd.NaT
    return df

def consolidar_inspecoes_sem_duplicar(df):
    # Inspecionados - pega só a última inspeção por técnico + produto
    com_data = df[df['DATA_INSPECAO'].notnull()].copy()
    com_data = com_data.sort_values(by='DATA_INSPECAO', ascending=False)
    com_data = com_data.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], keep='first')

    # Pendentes - pega apenas quem NÃO tem inspeção e não apareceu nos inspecionados
    sem_data = df[df['DATA_INSPECAO'].isnull()].copy()
    chaves_usadas = com_data[['IDTEL_TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates()
    sem_data = sem_data.merge(chaves_usadas, on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR'], how='left', indicator=True)
    sem_data = sem_data[sem_data['_merge'] == 'left_only'].drop(columns=['_merge'])

    # Junta os dois
    df_final = pd.concat([com_data, sem_data], ignore_index=True)
    return df_final

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for nome, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=nome[:31], index=False)  # Nome da aba max 31 caracteres
    output.seek(0)
    return output

# URL do GitHub (RAW)
url_github = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

# Carregamento
df = carregar_dados_github(url_github)

colunas_necessarias = ['DATA_INSPECAO', 'IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'GERENTE', 'COORDENADOR']
if not all(col in df.columns for col in colunas_necessarias):
    st.error("Arquivo enviado não possui as colunas necessárias.")
    st.stop()

# Filtros
gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique())
coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique())

gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['GERENTE'] == gerente_selecionado]
if coordenador_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['COORDENADOR'] == coordenador_selecionado]

# Consolidar inspeções
df_consolidado = consolidar_inspecoes_sem_duplicar(df_filtrado)

# Separar
ultimas = df_consolidado[df_consolidado['DATA_INSPECAO'].notnull()]
nunca = df_consolidado[df_consolidado['DATA_INSPECAO'].isnull()]

# Métricas
total_registros = len(df_consolidado)
total_inspecionados = len(ultimas)
total_pendentes = len(nunca)
pct_inspecionados = (total_inspecionados / total_registros * 100) if total_registros else 0
pct_pendentes = (total_pendentes / total_registros * 100) if total_registros else 0

# Cards
col1, col2, col3 = st.columns(3)
col1.metric("Total Registros", total_registros)
col2.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
col3.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

# Gráfico pizza
fig = px.pie(
    names=["Inspecionados", "Pendentes"],
    values=[total_inspecionados, total_pendentes],
    color_discrete_sequence=["#4CAF50", "#FF6F61"],
    title="📊 Distribuição de Inspeções"
)
st.plotly_chart(fig, use_container_width=True)

# Tabelas
st.subheader("✅ Última Inspeção por Técnico + Produto")
st.dataframe(ultimas)

st.subheader("⚠️ Técnicos que Nunca Foram Inspecionados")
st.dataframe(nunca)

# Exportar Excel
output_excel = exportar_excel({
    'Consolidado': df_consolidado,
    'Ultima_Inspecao': ultimas,
    'Nunca_Inspecionados': nunca
})

st.download_button(
    label="⬇️ Baixar Excel com Resultados",
    data=output_excel,
    file_name="inspecoes_epi_resultado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
