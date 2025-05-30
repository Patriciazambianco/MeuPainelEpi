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

def cards_coloridos(total, pendentes, pct_ok, qtd_tecnicos_gerente, tecnicos_com_inspecao, tecnicos_sem_inspecao):
    card_style = """
        <div style="
            background-color: #4CAF50; 
            color: white; 
            padding: 15px; 
            border-radius: 10px; 
            text-align: center; 
            font-weight: bold;
            font-size: 28px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin: 5px;">
            {label}<br><span style='font-size:36px'>{value}</span>
        </div>
    """
    card_style_red = card_style.replace("#4CAF50", "#E74C3C")  # vermelho pendentes
    card_style_blue = card_style.replace("#4CAF50", "#3498DB") # azul técnicos com inspeção
    card_style_grey = card_style.replace("#4CAF50", "#7F8C8D") # cinza técnicos sem inspeção

    cols = st.columns(6)

    cols[0].markdown(card_style.format(label="Total Inspeções", value=total), unsafe_allow_html=True)
    cols[1].markdown(card_style_red.format(label="Pendentes", value=pendentes), unsafe_allow_html=True)
    cols[2].markdown(card_style.format(label="% OK", value=f"{pct_ok:.1f}%"), unsafe_allow_html=True)
    cols[3].markdown(card_style.format(label="Técnicos Gerente", value=qtd_tecnicos_gerente), unsafe_allow_html=True)
    cols[4].markdown(card_style_blue.format(label="Técnicos com Inspeção", value=tecnicos_com_inspecao), unsafe_allow_html=True)
    cols[5].markdown(card_style_grey.format(label="Técnicos sem Inspeção", value=tecnicos_sem_inspecao), unsafe_allow_html=True)

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

    cards_coloridos(total, pendentes, pct_ok, qtd_tecnicos_gerente, tecnicos_com_inspecao, tecnicos_sem_inspecao)

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=300)

    st.subheader("📈 % Check List OK e Pendentes por Gerente")
    df_pie = df_filtrado.groupby('GERENTE_IMEDIATO')['Status_Final'].value_counts().unstack().fillna(0)
    for gerente in df_pie.index:
        st.markdown(f"**👨‍💼 {gerente}**")
        fig = px.pie(
            names=df_pie.columns,
            values=df_pie.loc[gerente],
            title=f"Status - {gerente}",
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

