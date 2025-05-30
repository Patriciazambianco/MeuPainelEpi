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

    # Base com todos os pares TECNICO + PRODUTO
    base = df[['TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates()

    # Última inspeção válida
    ultimas = (
        df.dropna(subset=['Data_Inspecao'])
        .sort_values('Data_Inspecao')
        .groupby(['TECNICO', 'PRODUTO_SIMILAR'], as_index=False)
        .last()
    )

    # Junta com a base para manter os sem inspeção
    final = pd.merge(base, ultimas, on=['TECNICO', 'PRODUTO_SIMILAR'], how='left')

    # Padroniza status
    final['Status_Final'] = final['Status_Final'].str.upper()

    # Cria coluna de pendência vencida
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

    # Filtro por gerente com opção "Todos"
    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerentes.insert(0, "Todos")
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", gerentes)

    if gerente_sel == "Todos":
        df_gerente = df.copy()
    else:
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    # Filtro por coordenador
    coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    # Filtro por produto
    produtos = sorted(df_gerente['PRODUTO_SIMILAR'].dropna().unique())
    produto_sel = st.sidebar.multiselect("📦 Produto", options=produtos, default=produtos)

    # Filtro por técnico
    tecnicos = sorted(df_gerente['TECNICO'].dropna().unique())
    tecnico_sel = st.sidebar.multiselect("👷 Técnico", options=tecnicos, default=tecnicos)

    # Filtro vencidos
    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")

    # Aplicando todos os filtros
    df_filtrado = df_gerente[
        df_gerente['COORDENADOR'].isin(coord_sel) &
        df_gerente['PRODUTO_SIMILAR'].isin(produto_sel) &
        df_gerente['TECNICO'].isin(tecnico_sel)
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

    # Dados detalhados + download
    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Gráfico de barras
    st.subheader("📦 Inspeções por Produto")
    if not df_filtrado.empty:
        fig = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status_Final", barmode="group",
                           color_discrete_map={"OK": "green", "PENDENTE": "red"})
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

if __name__ == "__main__":
    show()
