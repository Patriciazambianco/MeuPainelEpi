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

    # --- FILTROS ---
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

    # --- DOWNLOAD BUTTON NO TOPO ---
    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- CARDS COLORIDOS ---
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    num_tecnicos = df_filtrado['TECNICO'].nunique()
    tecnicos_inspecionaram = df_filtrado[df_filtrado['Data_Inspecao'].notnull()]['TECNICO'].nunique()
    tecnicos_nao_inspecionaram = num_tecnicos - tecnicos_inspecionaram

    col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,1])

    def color_metric(label, value, color):
        st.markdown(f"""
        <div style='
            padding:15px; 
            border-radius:10px; 
            background-color:{color}; 
            color:white; 
            text-align:center;
            font-family:sans-serif;
            '>
            <h5 style='margin-bottom:5px'>{label}</h5>
            <h2 style='margin-top:0'>{value}</h2>
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

    # --- SEUS GRÁFICOS E TABELAS AQUI ---
    # Por exemplo:
    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
