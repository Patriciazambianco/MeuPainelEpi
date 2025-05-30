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

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", options=["Todos"] + gerentes)

    if gerente_sel == "Todos":
        df_gerente = df.copy()
    else:
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    tecnicos = sorted(df_gerente['TECNICO'].dropna().unique())
    tecnico_sel = st.sidebar.multiselect("👷‍♂️ Técnico", options=tecnicos, default=tecnicos)

    df_filtrado = df_gerente[df_gerente['TECNICO'].isin(tecnico_sel)]

    # Filtro vencidos > 180 dias
    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido'] == True]

    # Indicadores
    st.subheader("📌 Indicadores Gerais")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    qtd_tecnicos_gerente = df_gerente['TECNICO'].nunique()
    tecnicos_com_inspecao = df_filtrado.dropna(subset=['Data_Inspecao'])['TECNICO'].nunique()
    tecnicos_sem_inspecao = qtd_tecnicos_gerente - tecnicos_com_inspecao

    col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,1])
    col1.metric("Total Inspeções", total)
    col2.metric("Pendentes", pendentes)
    col3.metric("% OK", f"{pct_ok:.1f}%")
    col4.metric("Técnicos Gerente", qtd_tecnicos_gerente)
    col5.metric("Técnicos com Inspeção", tecnicos_com_inspecao)
    col6.metric("Técnicos sem Inspeção", tecnicos_sem_inspecao)

    # Dados detalhados antes dos gráficos
    st.subheader("📋 Dados Detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=300)

    # Gráfico % Checklists por dia e gerente
    st.subheader("📅 % Checklists por Dia e Gerente")
    df_datas = df_filtrado.dropna(subset=['Data_Inspecao']).copy()
    if not df_datas.empty:
        df_agg = (
            df_datas.groupby(['Data_Inspecao', 'GERENTE_IMEDIATO'])
            .agg(total_inspecoes=('Status_Final', 'count'),
                 ok_inspecoes=('Status_Final', lambda x: (x == 'OK').sum()))
            .reset_index()
        )
        df_agg['pct_ok'] = (df_agg['ok_inspecoes'] / df_agg['total_inspecoes']) * 100

        fig = px.line(
            df_agg,
            x='Data_Inspecao',
            y='pct_ok',
            color='GERENTE_IMEDIATO',
            markers=True,
            labels={'pct_ok': '% Checklists OK', 'Data_Inspecao': 'Data da Inspeção', 'GERENTE_IMEDIATO': 'Gerente'},
            title='% Checklists OK ao longo do tempo por Gerente'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado de inspeção disponível para o filtro selecionado.")

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

    # Exportação Excel
    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    show()
