import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df['Data_Inspecao'] = pd.to_datetime(df['DATA_INSPECAO'])
    return df

def show():
    st.title("📊 Dashboard de Inspeções por Gerência")

    df = carregar_dados()

    gerentes_foco = [
        "ADENILSON JOSE DA SILVA",
        "IRINEU TORREGROSSA CLEMENTE JUNIOR",
        "ALEX MENDONCA BARRETO"
    ]

    gerente_sel = st.sidebar.selectbox("Gerente", gerentes_foco)

    df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coords = df_gerente['COORDENADOR_IMEDIATO'].dropna().unique()
    coord_sel = st.sidebar.multiselect("Coordenador", options=coords, default=coords)

    df_filtrado = df_gerente[df_gerente['COORDENADOR_IMEDIATO'].isin(coord_sel)]

    st.subheader("Indicadores Gerais")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status'] == 'Pendente').sum()
    pct_ok = (df_filtrado['Status'] == 'OK').mean() * 100 if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Inspeções", total)
    col2.metric("Pendentes", pendentes)
    col3.metric("% OK", f"{pct_ok:.1f}%")

    st.subheader("Inspeções por Produto")
    fig = px.histogram(df_filtrado, x="Produto", color="Status", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
