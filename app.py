import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de EPI", layout="wide")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'Status'
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

    return final

def show():
    st.title("🦺 Dashboard de EPI")

    df = carregar_dados()

    col_filtro1, col_filtro2 = st.sidebar.columns(2)
    gerentes_foco = sorted(df['GERENTE_IMEDIATO'].dropna().unique())
    gerente_sel = col_filtro1.selectbox("Gerente", gerentes_foco)

    df_gerente = df[df['GERENTE_IMEDIATO'] == gerente_sel]

    coords = sorted(df_gerente['COORDENADOR'].dropna().unique())
    coord_sel = col_filtro2.multiselect("Coordenador", options=coords, default=coords)

    df_filtrado = df_gerente[df_gerente['COORDENADOR'].isin(coord_sel)]

    st.markdown("### 📊 Indicadores Gerais")
    total = df_filtrado.shape[0]
    pendentes = (df_filtrado['Status'] == 'Pendente').sum()
    ok = (df_filtrado['Status'] == 'OK').sum()
    pct_ok = (ok / total) * 100 if total > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Inspeções", total)
    kpi2.metric("Pendentes", pendentes)
    kpi3.metric("% OK", f"{pct_ok:.1f}%")

    st.markdown("### 📊 Inspeções por Produto")
    fig_produto = px.histogram(df_filtrado, x="PRODUTO_SIMILAR", color="Status", barmode="group")
    st.plotly_chart(fig_produto, use_container_width=True)

    st.markdown("### 🌐 Status por Gerente")
    df_gerente_pie = df.groupby('GERENTE_IMEDIATO')['Status'].value_counts().unstack().fillna(0)
    for gerente in df_gerente_pie.index:
        st.markdown(f"**{gerente}**")
        fig = px.pie(
            names=df_gerente_pie.columns,
            values=df_gerente_pie.loc[gerente],
            title=f"Status - {gerente}",
            hole=0.4,
            color_discrete_map={"OK": "green", "Pendente": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🛋️ Status por Coordenador")
    df_coord_pie = df.groupby('COORDENADOR')['Status'].value_counts().unstack().fillna(0)
    for coord in df_coord_pie.index:
        st.markdown(f"**{coord}**")
        fig = px.pie(
            names=df_coord_pie.columns,
            values=df_coord_pie.loc[coord],
            title=f"Status - {coord}",
            hole=0.4,
            color_discrete_map={"OK": "green", "Pendente": "red"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📄 Dados Detalhados")
    st.dataframe(df_filtrado.reset_index(drop=True), height=400)

if __name__ == "__main__":
    show()
