import pandas as pd
import streamlit as st
import plotly.express as px
from io import BytesIO
import requests

@st.cache_data
def carregar_dados_github(https://github.com/Patriciazambianco/MeuPainelEpi/blob/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx):
    response = requests.get(url)
    response.raise_for_status()
    df = pd.read_excel(BytesIO(response.content))
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df.loc[df['DATA_INSPECAO'] == pd.Timestamp('2001-01-01'), 'DATA_INSPECAO'] = pd.NaT
    return df

@st.cache_data
def carregar_dados_local(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df.loc[df['DATA_INSPECAO'] == pd.Timestamp('2001-01-01'), 'DATA_INSPECAO'] = pd.NaT
    return df

def consolidar_ultima_inspecao_ou_pendente(df):
    # Ordena para garantir consistência na seleção
    df_sorted = df.sort_values(by=['DATA_INSPECAO', 'IDTEL_TECNICO'], ascending=[False, True])
    max_datas = df_sorted.groupby(['IDTEL_TECNICO', 'PRODUTO_SIMILAR'])['DATA_INSPECAO'].max().reset_index()
    df_max = pd.merge(df_sorted, max_datas, on=['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'], how='inner')
    df_final = df_max.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR']).reset_index(drop=True)
    return df_final

def gerar_nunca_inspecionados(df):
    return df[df['DATA_INSPECAO'].isnull()]

def exportar_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    output.seek(0)
    return output

st.set_page_config(page_title="Dashboard EPI", layout="wide")
st.title("📋 Dashboard de Inspeções de EPI")

url_github = "https://raw.githubusercontent.com/usuario/repositorio/branch/caminho/arquivo.xlsx"

usar_github = st.checkbox("Carregar dados direto do GitHub", value=True)

if usar_github:
    try:
        df = carregar_dados_github(url_github)
    except Exception as e:
        st.error(f"Erro ao carregar dados do GitHub: {e}")
        st.stop()
else:
    uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com os dados", type="xlsx")
    if uploaded_file:
        df = carregar_dados_local(uploaded_file)
    else:
        st.info("Por favor, envie um arquivo Excel ou selecione a opção GitHub.")
        st.stop()

colunas_necessarias = ['DATA_INSPECAO', 'IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'GERENTE', 'COORDENADOR']
if not all(col in df.columns for col in colunas_necessarias):
    st.error("Arquivo enviado não possui as colunas necessárias.")
    st.stop()

gerentes = ['Todos'] + sorted(df['GERENTE'].dropna().unique())
coordenadores = ['Todos'] + sorted(df['COORDENADOR'].dropna().unique())

gerente_selecionado = st.selectbox("Filtrar por Gerente", gerentes)
coordenador_selecionado = st.selectbox("Filtrar por Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['GERENTE'] == gerente_selecionado]
if coordenador_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['COORDENADOR'] == coordenador_selecionado]

ultimas = consolidar_ultima_inspecao_ou_pendente(df_filtrado)
nunca = gerar_nunca_inspecionados(df_filtrado)

total_registros = len(df_filtrado)
total_inspecionados = len(ultimas)
total_pendentes = len(nunca)
pct_inspecionados = (total_inspecionados / total_registros * 100) if total_registros else 0
pct_pendentes = (total_pendentes / total_registros * 100) if total_registros else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Registros", total_registros)
col2.metric("Inspecionados (%)", f"{pct_inspecionados:.1f}%")
col3.metric("Pendentes (%)", f"{pct_pendentes:.1f}%")

fig = px.pie(
    names=["Inspecionados", "Pendentes"],
    values=[total_inspecionados, total_pendentes],
    color_discrete_sequence=["#4CAF50", "#FF6F61"],
    title="📊 Distribuição de Inspeções"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("✅ Última Inspeção por Técnico + Produto")
st.dataframe(ultimas)

st.subheader("⚠️ Técnicos que Nunca Foram Inspecionados ou com Data 01/01/2001")
st.dataframe(nunca)

output_excel = exportar_excel({'Ultima_Inspecao': ultimas, 'Nunca_Inspecionados': nunca})

st.download_button(
    label="⬇️ Baixar Excel com Resultados",
    data=output_excel,
    file_name="inspecoes_epi_resultado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

