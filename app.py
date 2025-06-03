import pandas as pd
import streamlit as st

# Carrega dados do Excel
@st.cache_data
def carregar_dados_local(caminho):
    df = pd.read_excel(caminho, engine="openpyxl")
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df['PRODUTO_SIMILAR'] = df['PRODUTO_SIMILAR'].astype(str).str.strip().str.upper()
    return df

# Remove duplicatas exatas (mesmo técnico, produto e data de inspeção)
def remover_duplicatas(df):
    return df.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'])

# Caminho do arquivo
caminho_arquivo = "/mnt/data/LISTA DE VERIFICAÇÃO EPI.xlsx"
df = carregar_dados_local(caminho_arquivo)

# Aplica a lógica para tirar duplicatas
inspecoes_sem_duplicatas = remover_duplicatas(df[df['DATA_INSPECAO'].notnull()])

# STREAMLIT APP
st.set_page_config(page_title="Inspeções EPI", layout="wide")
st.title("📋 Todas as Inspeções Realizadas (sem duplicatas exatas)")

# Mostra resultado
st.dataframe(inspecoes_sem_duplicatas)

# Baixar Excel
st.download_button(
    label="⬇️ Baixar Excel sem Duplicatas",
    data=inspecoes_sem_duplicatas.to_excel(index=False, engine='xlsxwriter'),
    file_name="inspecoes_sem_duplicatas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
