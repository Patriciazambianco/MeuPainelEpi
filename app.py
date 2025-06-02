import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

@st.cache_data

def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TÉCNICO, PRODUTO e INSPEÇÃO.")
        return pd.DataFrame()

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'STATUS CHECK LIST'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Separar os que têm data
    df_com_data = df.dropna(subset=['Data_Inspecao']).copy()
    df_sem_data = df[df['Data_Inspecao'].isna()].copy()

    # Obter a última por técnico + produto
    df_com_data.sort_values('Data_Inspecao', ascending=True, inplace=True)
    ultimos = df_com_data.groupby([tecnico_col, produto_col], as_index=False).last()

    # Juntar com os sem data (sem duplicar técnico+produto)
    base_sem_data = df_sem_data[[tecnico_col, produto_col]].drop_duplicates()
    base_sem_data = base_sem_data.merge(ultimos[[tecnico_col, produto_col]], on=[tecnico_col, produto_col], how='left', indicator=True)
    base_sem_data = base_sem_data[base_sem_data['_merge'] == 'left_only'].drop(columns=['_merge'])
    
    df_resultado = pd.concat([ultimos, df_sem_data.merge(base_sem_data, on=[tecnico_col, produto_col])], ignore_index=True)

    df_resultado.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    if 'STATUS CHECK LIST' in df_resultado.columns:
        df_resultado['STATUS CHECK LIST'] = df_resultado['STATUS CHECK LIST'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    df_resultado['Dias_Sem_Inspecao'] = (hoje - df_resultado['Data_Inspecao']).dt.days
    df_resultado['Vencido'] = df_resultado['Dias_Sem_Inspecao'] > 180

    return df_resultado

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes')
    return buffer.getvalue()

def plot_pie_chart(df, group_col, title_prefix):
    grouped = df.groupby(group_col)['STATUS CHECK LIST'].value_counts(dropna=False).unstack(fill_value=0)
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
    if df.empty:
        return

    gerentes = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        df = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coordenadores = sorted(df['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)
    df = df[df['COORDENADOR'].isin(coord_sel)]

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        df = df[df['Vencido']]

    df_pendentes = df[df['STATUS CHECK LIST'] == 'PENDENTE']
    st.download_button(
        label="📅 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    total = df.shape[0] if df.shape[0] > 0 else 1
    pct_pendentes = (df['STATUS CHECK LIST'] == 'PENDENTE').sum() / total * 100
    pct_ok = (df['STATUS CHECK LIST'] == 'OK').sum() / total * 100

    col1, col2 = st.columns(2)
    def color_metric(label, value, color, unit="%"):
        st.markdown(f"""
        <div style='
            padding:8px; 
            border-radius:10px; 
            background-color:{color}; 
            color:white; 
            text-align:center;
            font-family:sans-serif;
            font-size:13px;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.2);
            '>
            <h5 style='margin-bottom:4px'>{label}</h5>
            <h3 style='margin-top:0'>{value:.1f}{unit}</h3>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        color_metric("% OK", pct_ok, "#2a9d8f")
    with col2:
        color_metric("% Pendentes", pct_pendentes, "#e76f51")

    st.markdown("---")
    st.subheader("🍕 Status das Inspeções por Gerente")
    for i in range(0, len(set(df['GERENTE_IMEDIATO'])), 3):
        cols = st.columns(3)
        for j, fig in enumerate(plot_pie_chart(df, 'GERENTE_IMEDIATO', "Gerente")[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("🍕 Status das Inspeções por Coordenador")
    for i in range(0, len(set(df['COORDENADOR'])), 3):
        cols = st.columns(3)
        for j, fig in enumerate(plot_pie_chart(df, 'COORDENADOR', "Coordenador")[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Dados detalhados")
    st.dataframe(df.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
