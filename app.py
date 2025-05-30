import streamlit as st
import pandas as pd
import plotly.express as px
import io

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'Status'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')

    # Pega todos os pares Técnico + Produto
    base = df[['TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates()

    # Agrupa para pegar a última inspeção válida
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby(['TECNICO', 'PRODUTO_SIMILAR'], as_index=False)
        .last()
    )

    # Junta com a base para manter até quem não tem inspeção
    final = pd.merge(base, ultimas, on=['TECNICO', 'PRODUTO_SIMILAR'], how='left')

    # Status final com vencidos
    final['Dias_Sem_Inspecao'] = (pd.to_datetime("today") - final['Data_Inspecao']).dt.days
    final['Status_Final'] = final['Status']
    final.loc[final['Data_Inspecao'].isna(), 'Status_Final'] = 'Pendente'
    final.loc[final['Dias_Sem_Inspecao'] > 180, 'Status_Final'] = 'Pendente'

    return final

def show():
    st.set_page_config(page_title="Dashboard EPI", layout="wide")
    st.title("📊 Dashboard de Inspeções de EPI")

    df = carregar_dados()

    # Filtro lateral
    gerentes = df['GERENTE_IMEDIATO'].dropna().unique().tolist()
    gerente_sel = st.sidebar.selectbox("👔 Gerente", gerentes)

    df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coords = df_gerente['COORDENADOR'].dropna().unique().tolist()
    coord_sel = st.sidebar.multiselect("🧑‍💼 Coordenador", options=coords, default=coords)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    # KPIs
    st.subheader("📌 Indicadores Gerais")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'Pendente').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Inspeções", total)
    col2.metric("Pendentes", pendentes)
    col3.metric("% OK", f"{pct_ok:.1f}%")

    # Gráfico de barras por produto
    st.subheader("📦 Inspeções por Produto")
    fig = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status_Final", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    # Pizza por gerente
    st.subheader("🥧 Status por Gerente")
    df_gerente_pie = df.groupby('GERENTE_IMEDIATO')['Status_Final'].value_counts().unstack().fillna(0)

    for gerente in df_gerente_pie.index:
        st.markdown(f"**👨‍💼 {gerente}**")
        fig = px.pie(
            names=df_gerente_pie.columns,
            values=df_gerente_pie.loc[gerente],
            title=f"Status - {gerente}",
            hole=0.4,
            color_discrete_map={"OK": "green", "Pendente": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Pizza por coordenador
    st.subheader("🥧 Status por Coordenador")
    df_coord_pie = df.groupby('COORDENADOR')['Status_Final'].value_counts().unstack().fillna(0)

    for coord in df_coord_pie.index:
        st.markdown(f"**👩‍💼 {coord}**")
        fig = px.pie(
            names=df_coord_pie.columns,
            values=df_coord_pie.loc[coord],
            title=f"Status - {coord}",
            hole=0.4,
            color_discrete_map={"OK": "green", "Pendente": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tabela
    st.subheader("📋 Dados Detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

    # Botão de exportar pendentes
    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'Pendente']

    if not df_pendentes.empty:
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
            df_pendentes.to_excel(writer, index=False, sheet_name='Pendentes')
        towrite.seek(0)
        st.download_button(
            label="📤 Exportar Pendentes para Excel",
            data=towrite,
            file_name="pendencias_epi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("✅ Nenhuma pendência encontrada nos filtros aplicados.")

if __name__ == "__main__":
    show()


