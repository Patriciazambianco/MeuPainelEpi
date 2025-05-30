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

def card(title, value, color):
    return f"""
    <div style="background-color:{color}; padding:12px; border-radius:10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.1); text-align:center">
        <h5 style="margin:0; color:white;">{title}</h5>
        <h3 style="margin:5px 0 0 0; color:white;">{value}</h3>
    </div>
    """

def show():
    st.title("📊 Dashboard de Inspeções EPI")

    df = carregar_dados()

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerentes.insert(0, "Todos")
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", gerentes)

    if gerente_sel == "Todos":
        df_gerente = df.copy()
    else:
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    produtos = sorted(df_gerente['PRODUTO_SIMILAR'].dropna().unique())
    produto_sel = st.sidebar.multiselect("📦 Produto", options=produtos, default=produtos)

    tecnicos = sorted(df_gerente['TECNICO'].dropna().unique())
    tecnico_sel = st.sidebar.multiselect("👷 Técnico", options=tecnicos, default=tecnicos)

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")

    df_filtrado = df_gerente[
        df_gerente['COORDENADOR'].isin(coord_sel) &
        df_gerente['PRODUTO_SIMILAR'].isin(produto_sel) &
        df_gerente['TECNICO'].isin(tecnico_sel)
    ]

    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido'] == True]

    st.subheader("📌 Indicadores Gerais")

    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    tecnicos_gerente = df_gerente['TECNICO'].nunique()
    tecnicos_com_inspecao = df_gerente.dropna(subset=['Data_Inspecao'])['TECNICO'].nunique()
    tecnicos_sem_inspecao = tecnicos_gerente - tecnicos_com_inspecao

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(card("📊 Total Inspeções", total, "#1f77b4"), unsafe_allow_html=True)
    with col2:
        st.markdown(card("❌ Pendentes", pendentes, "#d62728"), unsafe_allow_html=True)
    with col3:
        st.markdown(card("✅ % OK", f"{pct_ok:.1f}%", "#2ca02c"), unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown(card("👷 Técnicos do gerente", tecnicos_gerente, "#9467bd"), unsafe_allow_html=True)
    with col5:
        st.markdown(card("📋 Com inspeção", tecnicos_com_inspecao, "#17becf"), unsafe_allow_html=True)
    with col6:
        st.markdown(card("🚫 Sem inspeção", tecnicos_sem_inspecao, "#ff7f0e"), unsafe_allow_html=True)

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("📦 Inspeções por Produto")
    if not df_filtrado.empty:
        fig = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status_Final", barmode="group",
                           color_discrete_map={"OK": "green", "PENDENTE": "red"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

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

