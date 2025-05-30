import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'Status'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    base = df[['TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates()

    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby(['TECNICO', 'PRODUTO_SIMILAR'], as_index=False)
        .last()
    )

    final = pd.merge(base, ultimas, on=['TECNICO', 'PRODUTO_SIMILAR'], how='left')

    # Cria coluna "Dias desde a última inspeção"
    final["Dias_Desde"] = (datetime.today() - final['Data_Inspecao']).dt.days

    # Define status vencido
    final["Vencido"] = final["Dias_Desde"] > 180
    final["Status_Final"] = final["Status"].fillna("Sem Inspeção")
    final.loc[final["Vencido"] == True, "Status_Final"] = "Pendente"

    return final

def show():
    st.set_page_config(page_title="Dashboard EPI", layout="wide")
    st.title("📊 Dashboard de Inspeções EPI")

    df = carregar_dados()

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Gerente", gerentes)

    df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coords = df_gerente['COORDENADOR'].dropna().unique()
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coords, default=coords)

    status_options = ["Todos", "OK", "Pendente", "Sem Inspeção"]
    status_sel = st.sidebar.selectbox("📋 Status da Inspeção", status_options)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    if status_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Status_Final'] == status_sel]

    st.subheader("📌 Indicadores")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'Pendente').sum()
    oks = (df_filtrado['Status_Final'] == 'OK').sum()
    sem_inspecao = (df_filtrado['Status_Final'] == 'Sem Inspeção').sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Registros", total)
    col2.metric("Pendentes", pendentes)
    col3.metric("OK", oks)
    col4.metric("Sem Inspeção", sem_inspecao)

    st.subheader("📦 Inspeções por Produto")
    if not df_filtrado.empty:
        fig = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status_Final", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

    st.subheader("🥧 Comparativo por Coordenador")
    if not df_filtrado.empty:
        df_pie = df_filtrado.groupby(['COORDENADOR', 'Status_Final']).size().reset_index(name='Contagem')
        for coord in df_pie['COORDENADOR'].unique():
            df_coord = df_pie[df_pie['COORDENADOR'] == coord]
            fig = px.pie(df_coord, names='Status_Final', values='Contagem', title=f"Status - {coord}", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum coordenador com dados disponíveis.")

    st.subheader("📋 Dados Detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()

