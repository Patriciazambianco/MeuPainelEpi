import streamlit as st
import pandas as pd
from io import BytesIO

# Link direto para o arquivo Excel no GitHub (versão RAW)
URL_GITHUB = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

@st.cache_data
def carregar_dados():
    df = pd.read_excel(URL_GITHUB, engine="openpyxl")
    return df

def filtrar_pendentes(df):
    # Troque 'Status' e 'Pendente' pelo nome da sua coluna e valor correto
    if 'Status' in df.columns:
        return df[df['Status'] == 'Pendente']
    else:
        st.warning("Coluna 'Status' não encontrada! Ajuste o nome da coluna no código.")
        return pd.DataFrame()  # retorna vazio se não achar a coluna

def gerar_excel_para_download(df):
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

def main():
    st.title("Painel EPI - Pendências")

    # Carrega os dados do Excel
    df_raw = carregar_dados()
    st.write("### Dados Originais")
    st.dataframe(df_raw.head())

    # Filtra pendentes
    df_pendentes = filtrar_pendentes(df_raw)
    st.write(f"### Pendentes ({len(df_pendentes)})")
    st.dataframe(df_pendentes)

    # Botão para download da planilha pendentes
    excel_bytes = gerar_excel_para_download(df_pendentes)
    st.download_button(
        label="Baixar Excel dos Pendentes",
        data=excel_bytes,
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    main()
