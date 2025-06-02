import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import unicodedata

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

def remove_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")

    # Normaliza nomes das colunas: remove acentos, espaços e coloca maiúsculas
    df.columns = [remove_acentos(col).strip().upper() for col in df.columns]

    st.write("🕵️‍♀️ Colunas encontradas no arquivo:", df.columns.tolist())

    # Identifica colunas TECNICO, PRODUTO, INSPECAO
    col_tec = [col for col in df.columns if 'TECNICO' in col]
    col_prod = [col for col in df.columns if 'PRODUTO' in col]
    col_data = [col for col in df.columns if 'INSPECAO' in col]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TECNICO, PRODUTO e INSPECAO (sem acentos).")
        return pd.DataFrame()

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    # Renomear colunas importantes (sem acento)
    rename_map = {}
    if 'GERENTE' in df.columns:
        rename_map['GERENTE'] = 'GERENTE_IMEDIATO'
    if 'SITUACAO CHECK LIST' in df.columns:
        rename_map['SITUACAO CHECK LIST'] = 'STATUS CHECK LIST'
    df.rename(columns=rename_map, inplace=True)

    df['DATA_INSPECAO'] = pd.to_datetime(df[data_col], errors='coerce')

    base = df[[tecnico_col, produto_col]].drop_duplicates()

    ultimas = (
        df.dropna(subset=['DATA_INSPECAO'])
        .sort_values('DATA_INSPECAO')
        .groupby([tecnico_col, produto_col], as_index=False)
        .last()
    )

    final = pd.merge(base, ultimas, on=[tecnico_col, produto_col], how='left')

    final.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    # Normaliza coluna STATUS CHECK LIST para maiúscula e tratar NaN
    final['STATUS CHECK LIST'] = final['STATUS CHECK LIST'].fillna('PENDENTE').str.upper()

    hoje = pd.Timestamp.now().normalize()
    final['DIAS_SEM_INSPECAO'] = (hoje - final['DATA_INSPECAO']).dt.days
    final['VENCIDO'] = final['DIAS_SEM_INSPECAO'] > 180

    # Colunas GERENTE_IMEDIATO e COORDENADOR (sem acento)
    if 'GERENTE_IMEDIATO' not in final.columns:
        final['GERENTE_IMEDIATO'] = "Sem Gerente"
    if 'COORDENADOR' not in final.columns:
        final['COORDENADOR'] = "Sem Coordenador"

    return final

def exportar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes')
    return buffer.getvalue()

def plot_pie_chart(df, group_col, title_prefix):
    grouped = df.groupby(group_col)['STATUS CHECK LIST'].value_counts().unstack(fill_value=0)
    # Garante que as colunas existam
    for col in ['OK', 'PENDENTE']:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped = grouped[['OK', 'PENDENTE']]

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
        df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]
    else:
        df_gerente = df.copy()

    coordenadores = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    # **Filtro para buscar pelo nome do técnico**
    nome_tec = st.sidebar.text_input("🔍 Buscar Técnico pelo nome")
    if nome_tec.strip() != "":
        df_filtrado['TECNICO'] = df_filtrado['TECNICO'].fillna('').astype(str)
        df_filtrado = df_filtrado[df_filtrado['TECNICO'].str.contains(nome_tec, case=False, na=False)]

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")
    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['VENCIDO']]

    df_pendentes = df_filtrado[df_filtrado['STATUS CHECK LIST'] == 'PENDENTE']
    st.download_button(
        label="📅 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    total = df_filtrado.shape[0] if df_filtrado.shape[0] > 0 else 1
    pct_pendentes = (df_filtrado['STATUS CHECK LIST'] == 'PENDENTE').sum() / total * 100
    pct_ok = (df_filtrado['STATUS CHECK LIST'] == 'OK').sum() / total * 100

    # Só os cards que você pediu: % OK e % Pendentes
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
    graficos_gerente = plot_pie_chart(df_filtrado, 'GERENTE_IMEDIATO', "Gerente")
    for i in range(0, len(graficos_gerente), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_gerente[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🍕 Status das Inspeções por Coordenador")
    graficos_coord = plot_pie_chart(df_filtrado, 'COORDENADOR', "Coordenador")
    for i in range(0, len(graficos_coord), 3):
        cols = st.columns(3)
        for j, fig in enumerate(graficos_coord[i:i+3]):
            cols[j].plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
