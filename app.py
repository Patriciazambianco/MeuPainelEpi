import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard EPI", layout="wide")

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

    return final

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Inspeções Vencidas")
    return buffer

def show():
    st.title("🦺 Dashboard de EPI - Pendências +180 dias")

    df = carregar_dados()
    hoje = pd.to_datetime(datetime.now().date())
    vencimento = hoje - timedelta(days=180)

    df['Status_180'] = df['Data_Inspecao'].apply(
        lambda x: "Pendente" if pd.isna(x) or x < vencimento else "OK"
    )

    df_vencidos = df[df['Status_180'] == 'Pendente']

    st.sidebar.header("🎯 Filtros")
    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione um Gerente", [""] + gerentes)

    if gerente_sel:
        df_gerente = df_vencidos[df_vencidos['GERENTE_IMEDIATO'] == gerente_sel]
        coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
        coord_sel = st.sidebar.multiselect("👩‍💼 Coordenadores", coordenadores, default=coordenadores)
        df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

        if not df_filtrado.empty:
            st.markdown("### ✅ Indicadores")
            total = df_filtrado.shape[0]

            col1, col2 = st.columns(2)
            col1.metric("Total Pendências > 180 dias", total)
            col2.download_button(
                "⬇️ Baixar Excel",
                data=exportar_excel(df_filtrado),
                file_name="pendencias_180_dias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("### 📦 Produtos com Pendência")
            fig_produto = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status_180", barmode="group")
            st.plotly_chart(fig_produto, use_container_width=True)

            st.markdown("### 🥧 Por Coordenador")
            df_coord_pie = df_filtrado.groupby('COORDENADOR')['Status_180'].value_counts().unstack().fillna(0)

            for coord in df_coord_pie.index:
                st.markdown(f"**👤 {coord}**")
                fig = px.pie(
                    names=df_coord_pie.columns,
                    values=df_coord_pie.loc[coord],
                    title=f"{coord} - Pendências",
                    hole=0.4,
                    color_discrete_map={"OK": "green", "Pendente": "red"}
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 Dados Detalhados")
            st.dataframe(df_filtrado.reset_index(drop=True), height=400)
        else:
            st.warning("Nenhuma pendência encontrada com os filtros selecionados.")
    else:
        st.info("Selecione um gerente para começar.")

if __name__ == "__main__":
    show()
