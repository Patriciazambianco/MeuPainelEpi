import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'Status_Final'
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
    final['Status_Final'] = final['Status_Final'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    final['Dias_Sem_Inspecao'] = (hoje - final['Data_Inspecao']).dt.days
    final['Vencido'] = final['Dias_Sem_Inspecao'] > 180

    return final

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes')
    return buffer.getvalue()

def show():
    st.title("📊 Dashboard de Inspeções EPI")
    df = carregar_dados()

    # Verifica reset de sessão
    if 'reset' in st.session_state and st.session_state.reset:
        st.session_state.clear()
        st.experimental_rerun()

    with st.sidebar:
        st.header("🎛️ Filtros")
        reset = st.button("🔄 Resetar Filtros")
        if reset:
            st.session_state['reset'] = True
            st.experimental_rerun()

        gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
        gerente_sel = st.selectbox("👨‍💼 Selecione o Gerente", options=["Todos"] + gerentes)

        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel] if gerente_sel != "Todos" else df.copy()

        coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
        coord_sel = st.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

        data_min = df_gerente['Data_Inspecao'].min()
        data_max = df_gerente['Data_Inspecao'].max()
        data_inicio, data_fim = st.date_input("📅 Período da Inspeção", [data_min, data_max])

        so_vencidos = st.checkbox("🔴 Mostrar apenas vencidos > 180 dias")

    df_filtrado = df_gerente[
        (df_gerente['COORDENADOR'].isin(coord_sel)) &
        (df_gerente['Data_Inspecao'] >= pd.to_datetime(data_inicio)) &
        (df_gerente['Data_Inspecao'] <= pd.to_datetime(data_fim))
    ]

    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido'] == True]

    # Indicadores
    st.subheader("📌 Indicadores Gerais")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Inspeções", total)
    col2.metric("Pendentes", pendentes)
    col3.metric("% OK", f"{pct_ok:.1f}%")

    # Gráfico por produto
    st.subheader("📦 Inspeções por Produto")
    if not df_filtrado.empty:
        fig = px.histogram(
            df_filtrado,
            x="PRODUTO_SIMILAR",
            color="Status_Final",
            barmode="group",
            color_discrete_map={"OK": "green", "PENDENTE": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

    # Pizza por Gerente
    st.subheader("🥧 Status por Gerente")
    df_gerente_pie = df.groupby('GERENTE_IMEDIATO')['Status_Final'].value_counts().unstack().fillna(0)
    for gerente in df_gerente_pie.index:
        st.markdown(f"**👨‍💼 {gerente}**")
        fig = px.pie(
            names=df_gerente_pie.columns,
            values=df_gerente_pie.loc[gerente],
            title=f"Status - {gerente}",
            hole=0.4,
            color_discrete_map={"OK": "green", "PENDENTE": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Pizza por Coordenador
    st.subheader("🥧 Status por Coordenador")
    df_coord_pie = df.groupby('COORDENADOR')['Status_Final'].value_counts().unstack().fillna(0)
    for coord in df_coord_pie.index:
        st.markdown(f"**👩‍💼 {coord}**")
        fig = px.pie(
            names=df_coord_pie.columns,
            values=df_coord_pie.loc[coord],
            title=f"Status - {coord}",
            hole=0.4,
            color_discrete_map={"OK": "green", "PENDENTE": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Exportação
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
