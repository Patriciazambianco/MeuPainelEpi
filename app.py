import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="Inspeções EPI", layout="wide")
st.title("📋 Todas as Inspeções Realizadas (sem duplicatas exatas)")

@st.cache_data
def carregar_dados_local(uploaded_file):
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df['DATA_INSPECAO'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    df['PRODUTO_SIMILAR'] = df['PRODUTO_SIMILAR'].astype(str).str.strip().str.upper()
    return df

def remover_duplicatas(df):
    return df.drop_duplicates(subset=['IDTEL_TECNICO', 'PRODUTO_SIMILAR', 'DATA_INSPECAO'])

def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Inspecoes')
    output.seek(0)
    return output

uploaded_file = st.file_uploader("📂 Envie o arquivo Excel com as inspeções", type=["xlsx"])

if uploaded_file:
    df = carregar_dados_local(uploaded_file)
    inspecoes_sem_duplicatas = remover_duplicatas(df[df['DATA_INSPECAO'].notnull()])

    st.success("✅ Arquivo carregado com sucesso!")

    st.subheader("✅ Inspeções (sem duplicatas exatas):")
    st.dataframe(inspecoes_sem_duplicatas)

    excel_bytes = exportar_excel(inspecoes_sem_duplicatas)

    st.download_button(
        label="⬇️ Baixar Excel sem Duplicatas",
        data=excel_bytes,
        file_name="inspecoes_sem_duplicatas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("⚠️ Por favor, envie o arquivo Excel com os dados de inspeção.")
