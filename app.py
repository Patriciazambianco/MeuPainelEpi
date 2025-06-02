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
    grouped = grouped[['OK', 'PENDENTE']] if set(['OK', 'PENDENTE']).issubset(grouped.columns) else grouped
    charts = []

    for grupo in grouped.index:
        valores = grouped.loc[grupo]
        fig = px.pie(
            names=valores.index,
            values=valores.values,
            color=valores.index,
            color_discrete_map={'OK': '#2a9d8f', 'PENDENTE': '#e76f51'},
            hole=0.4,
            title=f"{title_prefix}: {grupo}"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=250, showlegend=False)
        charts.append(fig)
    return charts

def show():
    st.title("📊 Dashboard de Inspeções EPI")

    df = carregar_dados()

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        df_gerente = df.copy()

    coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido']]

    # Exportar antes de qualquer coisa
    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Indicadores
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0
    num_tecnicos = df_filtrado['TECNICO'].nunique()
    tecnicos_inspecionaram = df_filtrado[df_filtrado['Data_Inspecao'].notnull()]['TECNICO'].nunique()
    tecnicos_nao_inspecionaram = num_tecnicos - tecnicos_inspecionaram

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    def color_metric(label, value, color):
        st.markdown(f"""
        <div style='
            padding:5px; 
            border-radius:6px; 
            background-color:{color}; 
            color:white; 
            text-align:center;
            font-family:sans-serif;
            font-size:13px;
            height:80px;
            '>
            <h5 style='margin-bottom:4px'>{label}</h5>
            <h3 style='margin-top:0'>{value}</h3>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        color_metric("Total Inspeções", total, "#2a9d8f")
    with col2:
        color_metric("Pendentes", pendentes, "#e76f51")
    with col3:
        color_metric("% OK", f"{pct_ok:.1f}%", "#264653")
    with col4:
        color_metric("Técnicos", num_tecnicos, "#f4a261")
    with col5:
        color_metric("Téc. que Inspecionaram", tecnicos_inspecionaram, "#2a9d8f")
    with col6:
        color_metric("Téc. não Inspecionaram", tecnicos_nao_inspecionaram, "#e76f51")

    st.markdown("---")

    # Gráfico de tendência
    st.subheader("📈 Tendência de % OK e Pendentes ao Longo do Tempo")

    agrupamento = st.selectbox("Agrupar por:", ["Dia", "Semana", "Mês"])
    df_tendencia = df_filtrado.dropna(subset=['Data_Inspecao']).copy()

    if agrupamento == "Semana":
        df_tendencia['Periodo'] = df_tendencia['Data_Inspecao'].dt.to_period('W').apply(lambda r: r.start_time)
    elif agrupamento == "Mês":
        df_tendencia['Periodo'] = df_tendencia['Data_Inspecao'].dt.to_period('M').apply(lambda r: r.start_time)
    else:
        df_tendencia['Periodo'] = df_tendencia['Data_Inspecao']

    tendencia = (
        df_tendencia
        .groupby(['Periodo', 'Status_Final'])
        .size()
        .reset_index(name='count')
        .pivot(index='Periodo', columns='Status_Final', values='count')
        .fillna(0)
    )

    tendencia['% OK'] = tendencia['OK'] / tendencia.sum(axis=1) * 100
    tendencia['% PENDENTE'] = tendencia['PENDENTE'] / tendencia.sum(axis=1) * 100
    tendencia = tendencia[['% OK', '% PENDENTE']].reset_index()

    fig_tendencia = px.line(
        tendencia,
        x='Periodo',
        y=['% OK', '% PENDENTE'],
        markers=True,
        color_discrete_map={'% OK': '#2a9d8f', '% PENDENTE': '#e76f51'}
    )
    fig_tendencia.update_layout(xaxis_title="Data", yaxis_title="Porcentagem", legend_title="Status")
    st.plotly_chart(fig_tendencia, use_container_width=True)

    st.markdown("---")
    st.subheader("🍕 Status das Inspeções por Gerente")
    for i in range(0, len(graficos := plot_pie_chart(df_filtrado, 'GERENTE_IMEDIATO', "Gerente")), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🍕 Status das Inspeções por Coordenador")
    for i in range(0, len(graficos := plot_pie_chart(df_filtrado, 'COORDENADOR', "Coordenador")), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
