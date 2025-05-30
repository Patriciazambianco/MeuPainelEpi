import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()
    df.rename(columns={'GERENTE': 'GERENTE_IMEDIATO', 'SITUAÇÃO CHECK LIST': 'Status_Final'}, inplace=True)
    df['Data_Inspecao'] = pd.to_datetime(df['DATA_INSPECAO'], errors='coerce')
    base = df[['TECNICO', 'PRODUTO_SIMILAR']].drop_duplicates()
    ultimas = (df.dropna(subset=['Data_Inspecao'])
               .sort_values('Data_Inspecao')
               .groupby(['TECNICO', 'PRODUTO_SIMILAR'], as_index=False).last())
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

def cards_estilos(label, valor, cor_fundo):
    estilo = f"""
    <div style="
        background-color: {cor_fundo};
        padding: 20px 15px;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-weight: 600;
        font-size: 22px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        ">
        <div style="font-size:16px; opacity: 0.85;">{label}</div>
        <div style="font-size:36px; margin-top:5px;">{valor}</div>
    </div>
    """
    return estilo

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

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    if so_vencidos:
        df_filtrado = df_filtrado[df_filtrado['Vencido'] == True]

    # Indicadores
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status_Final'] == 'PENDENTE').sum()
    pct_ok = (df_filtrado['Status_Final'] == 'OK').mean() * 100 if total > 0 else 0

    qtd_tecnicos_gerente = df_gerente['TECNICO'].nunique()
    tecnicos_com_inspecao = df_filtrado.dropna(subset=['Data_Inspecao'])['TECNICO'].nunique()
    tecnicos_sem_inspecao = qtd_tecnicos_gerente - tecnicos_com_inspecao

    # Botão Baixar pendentes no topo
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_download_top"
    )

    # Cards indicadores
    cols = st.columns([1,1,1,1,1,1])
    cores = ["#2E86C1", "#E74C3C", "#27AE60", "#34495E", "#1ABC9C", "#7F8C8D"]
    valores = [total, pendentes, f"{pct_ok:.1f}%", qtd_tecnicos_gerente, tecnicos_com_inspecao, tecnicos_sem_inspecao]
    labels = ["Total Inspeções", "Pendentes", "% OK", "Técnicos Gerente", "Técnicos com Inspeção", "Técnicos sem Inspeção"]

    for col, label, valor, cor in zip(cols, labels, valores, cores):
        col.markdown(cards_estilos(label, valor, cor), unsafe_allow_html=True)

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=300)

    st.subheader("📈 % Check List OK e Pendentes")

    col1, col2 = st.columns(2)

    # Gráfico por Gerente
    df_ger = df_filtrado.groupby('GERENTE_IMEDIATO')['Status_Final'].value_counts().unstack().fillna(0)
    with col1:
        st.markdown("### 👨‍💼 Por Gerente")
        for gerente in df_ger.index:
            fig = px.pie(
                names=df_ger.columns,
                values=df_ger.loc[gerente],
                title=f"Status - {gerente}",
                hole=0.4,
                color_discrete_map={"OK": "green", "PENDENTE": "red"}
            )
            st.plotly_chart(fig, use_container_width=True)

    # Gráfico por Coordenador
    df_coord = df_filtrado.groupby('COORDENADOR')['Status_Final'].value_counts().unstack().fillna(0)
    with col2:
        st.markdown("### 👩‍💼 Por Coordenador")
        for coord in df_coord.index:
            fig = px.pie(
                names=df_coord.columns,
                values=df_coord.loc[coord],
                title=f"Status - {coord}",
                hole=0.4,
                color_discrete_map={"OK": "green", "PENDENTE": "red"}
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show()
