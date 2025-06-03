import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- Fundo colorido customizado via CSS ---
page_bg = """
<style>
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
h1, h2, h3, h4, h5, h6, .stMetric-label {
    color: white !important;
}
.stButton>button {
    background-color: #ff5722;
    color: white;
    font-weight: bold;
    border-radius: 8px;
}
.stButton>button:hover {
    background-color: #e64a19;
}
.blink {
    animation: blink-animation 1.5s steps(5, start) infinite;
    -webkit-animation: blink-animation 1.5s steps(5, start) infinite;
}
@keyframes blink-animation {
    to {
        visibility: hidden;
    }
}
@-webkit-keyframes blink-animation {
    to {
        visibility: hidden;
    }
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# --- Função para carregar dados direto do GitHub ---
@st.cache_data
def carregar_dados():
    url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# --- Função para filtrar última inspeção por TÉCNICO ---
def filtrar_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

    # separa os com e sem inspeção
    com_data = df[df["DATA_INSPECAO"].notna()]
    sem_data = df[df["DATA_INSPECAO"].isna()]

    # pega apenas a última por TÉCNICO
    ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")

    # filtra os sem inspeção que ainda não existem em ultimas
    sem_data = sem_data.merge(ultimas[["TÉCNICO"]], on=["TÉCNICO"], how="left", indicator=True)
    apenas_sem = sem_data[sem_data['_merge'] == 'left_only'].drop(columns=['_merge'])

    # concatena o resultado final
    resultado = pd.concat([ultimas, apenas_sem], ignore_index=True)
    return resultado

# --- Função para gerar o Excel com somente pendentes ---
def gerar_download_excel_pendentes(df):
    pendentes = df[df["DATA_INSPECAO"].isna()]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pendentes.to_excel(writer, index=False, sheet_name="Pendentes")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a class="blink" href="data:application/octet-stream;base64,{b64}" download="pendencias_inspecoes.xlsx">📥 Baixar Excel só Pendentes</a>'
    return href

# --- Início do app ---
st.title("🦺 Inspeções EPI")

# Botão download pendentes no topo
df_raw = carregar_dados()
df_tratado = filtrar_por_tecnico(df_raw)
st.markdown(gerar_download_excel_pendentes(df_tratado), unsafe_allow_html=True)

# Filtros
col1, col2 = st.columns(2)
gerentes = df_tratado["GERENTE"].dropna().unique()
coordenadores = df_tratado["COORDENADOR"].dropna().unique()

with col1:
    gerente_sel = st.multiselect("Filtrar por Gerente", sorted(gerentes))
with col2:
    coordenador_sel = st.multiselect("Filtrar por Coordenador", sorted(coordenadores))

df_filtrado = df_tratado.copy()
if gerente_sel:
    df_filtrado = df_filtrado[df_filtrado["GERENTE"].isin(gerente_sel)]
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

# KPIs
total = len(df_filtrado)
pending = df_filtrado["DATA_INSPECAO"].isna().sum()
ok = total - pending
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendente = round(100 - pct_ok, 1) if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Inspeções OK", ok)
col2.metric("Pendentes", pending)
col3.metric("% OK", f"{pct_ok}%")

# Gráficos de pizza por GERENTE e COORDENADOR
def grafico_pizza_por_col(df, coluna, titulo):
    dados = df.groupby(coluna)["DATA_INSPECAO"].apply(
        lambda x: pd.Series({
            "OK": x.notna().sum(),
            "Pendente": x.isna().sum()
        })
    ).reset_index()
    fig = px.pie(
        dados.melt(id_vars=coluna, value_vars=["OK", "Pendente"]),
        names="variable",
        values="value",
        color="variable",
        color_discrete_map={"OK": "green", "Pendente": "red"},
        title=titulo,
        facet_col=coluna,
        facet_col_wrap=3
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(margin=dict(t=50,b=0,l=0,r=0), legend_title_text='Status')
    return fig

st.markdown("### Status das Inspeções por Gerente")
st.plotly_chart(grafico_pizza_por_col(df_filtrado, "GERENTE", "Status por Gerente"), use_container_width=True)

st.markdown("### Status das Inspeções por Coordenador")
st.plotly_chart(grafico_pizza_por_col(df_filtrado, "COORDENADOR", "Status por Coordenador"), use_container_width=True)

# Tabela final com filtro
st.markdown("### Dados Tratados")
st.dataframe(df_filtrado, use_container_width=True)
