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
    gerente_sel = st.sidebar.selectbox("👨‍💼 Selecione o Gerente", ["Todos"] + gerentes)

    if gerente_sel != "Todos":
        df = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coordenadores = sorted(df['COORDENADOR'].dropna().unique())
    coord_sel = st.sidebar.multiselect("👩‍💼 Coordenador", options=coordenadores, default=coordenadores)

    so_vencidos = st.sidebar.checkbox("🔴 Mostrar apenas vencidos > 180 dias")

    df_filtrado = df[df['COORDENADOR'].isin(coord_sel)]

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

    st.subheader("📋 Dados detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

    # Download pendentes no topo
    df_pendentes = df_filtrado[df_filtrado['Status_Final'] == 'PENDENTE']
    st.download_button(
        label="📥 Baixar Pendentes (.xlsx)",
        data=exportar_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Gráficos de pizza coloridos
    st.subheader("🥧 % Check List OK e Pendentes por Gerente e Coordenador")

    color_map = {
        "OK": "#28a745",        # verde vibrante
        "PENDENTE": "#dc3545",  # vermelho forte
        "VENCIDO": "#fd7e14",   # laranja chamativo
    }

    # Gráfico por Gerente
    df_ger = df_filtrado.groupby('GERENTE_IMEDIATO')['Status_Final'].value_counts().unstack().fillna(0)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**👨‍💼 Gerentes**")
        for gerente in df_ger.index:
            st.markdown(f"**{gerente}**")
            fig = px.pie(
                names=df_ger.columns,
                values=df_ger.loc[gerente],
                title=f"Status - {gerente}",
                hole=0.4,
                color_discrete_map=color_map
            )
            fig.update_traces(textinfo='percent+label', textfont_size=14,
                              marker=dict(line=dict(color='#000000', width=1.5)))
            st.plotly_chart(fig, use_container_width=True)

    # Gráfico por Coordenador
    df_coord = df_filtrado.groupby('COORDENADOR')['Status_Final'].value_counts().unstack().fillna(0)
    with col2:
        st.markdown("**👩‍💼 Coordenadores**")
        for coord in df_coord.index:
            st.markdown(f"**{coord}**")
            fig = px.pie(
                names=df_coord.columns,
                values=df_coord.loc[coord],
                title=f"Status - {coord}",
                hole=0.4,
                color_discrete_map=color_map
            )
            fig.update_traces(textinfo='percent+label', textfont_size=14,
                              marker=dict(line=dict(color='#000000', width=1.5)))
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    show()
