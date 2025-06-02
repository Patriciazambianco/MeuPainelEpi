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

def plot_pie_chart(df, group_col, title_prefix):
    grouped = df.groupby(group_col)['Status_Final'].value_counts().unstack(fill_value=0)
    if 'OK' not in grouped.columns: grouped['OK'] = 0
    if 'PENDENTE' not in grouped.columns: grouped['PENDENTE'] = 0

    charts = []
    for grupo in grouped.index:
        valores = grouped.loc[grupo]
        fig = px.pie(
            names=valores.index,
            values=valores.values,
            color=valores.index,
            color_discrete_map={'OK':'#2a9d8f', 'PENDENTE':'#e76f51'},
            hole=0.4,
            title=f"{title_prefix}: {grupo}"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=30,b=0,l=0,r=0), height=250, showlegend=False)
        charts.append(fig)
    return charts

def show():
    st.title("\U0001F4CA Dashboard de Inspeções EPI")

    df = carregar_dados()

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("\U0001F468‍\U0001F4BC Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        df_gerente = df.copy()

    coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("\U0001F469‍\U0001F4BC Coordenador", options=coordenadores, default=coordenadores)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    so_vencidos = st.sidebar.checkbox("\U0001F534 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido']]

    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="\U0001F4E5 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    total = df_filtrado.shape[0] if df_filtrado.shape[0] > 0 else 1
    pct_pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum() / total * 100
    pct_ok = (df_filtrado['Status_Final'] == 'OK').sum() / total * 100

    num_tecnicos = df_filtrado['TECNICO'].nunique()
    tecnicos_inspecionaram = df_filtrado[df_filtrado['Data_Inspecao'].notnull()]['TECNICO'].nunique()
    pct_tecnicos_inspecionaram = tecnicos_inspecionaram / num_tecnicos * 100 if num_tecnicos > 0 else 0
    pct_tecnicos_nao_inspecionaram = 100 - pct_tecnicos_inspecionaram

    col1, col2, col3, col4 = st.columns(4)

    def color_metric(label, value, color):
        st.markdown(f"""
        <div style='
            padding:6px; 
            border-radius:10px; 
            background-color:{color}; 
            color:white; 
            text-align:center;
            font-family:sans-serif;
            font-size:13px;
            '>
            <h5 style='margin-bottom:4px'>{label}</h5>
            <h3 style='margin-top:0'>{value:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        color_metric("% OK", pct_ok, "#2a9d8f")
    with col2:
        color_metric("% Pendentes", pct_pendentes, "#e76f51")
    with col3:
        color_metric("% Técnicos com Inspeção", pct_tecnicos_inspecionaram, "#f4a261")
    with col4:
        color_metric("% Técnicos sem Inspeção", pct_tecnicos_nao_inspecionaram, "#e76f51")

    st.markdown("---")

    st.subheader("\U0001F355 Status das Inspeções por Gerente")
    graficos_gerente = plot_pie_chart(df_filtrado, 'GERENTE_IMEDIATO', "Gerente")
    for i in range(0, len(graficos_gerente), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_gerente[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("\U0001F355 Status das Inspeções por Coordenador")
    graficos_coord = plot_pie_chart(df_filtrado, 'COORDENADOR', "Coordenador")
    for i in range(0, len(graficos_coord), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_coord[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("\U0001F4CB Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
