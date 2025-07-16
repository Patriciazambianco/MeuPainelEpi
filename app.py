import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

# --- Configuração da página ---
st.set_page_config(page_title="Painel Técnico EPI - Deluxe", layout="wide", page_icon="🛠️")

# --- Tema Dark Customizado ---
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    .css-1d391kg {
        background-color: #1f1f1f !important;
    }
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 18px;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
        color: white;
    }
    .metric-label {
        color: #e0e0e0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Título ---
st.title("🛠️ Painel Técnico - Inspeções EPI (Deluxe Edition)")
st.markdown("---")

# --- Sidebar Navegação ---
page = st.sidebar.radio("Navegação", ["Visão Geral", "Ranking por Coordenador", "Ranking por Produto", "Dados Detalhados"])

# --- Carregamento de Dados ---
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# --- Preprocessamento ---
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Última inspeção por técnico + produto
ultima = df.sort_values(["TECNICO", "DATA_INSPECAO"], ascending=[True, False])
ultima = ultima.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# Técnicos com e sem inspeção (garantir 1 linha por técnico + produto)
tecnicos = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="last")[
    ["TECNICO", "COORDENADOR", "GERENTE", "PRODUTO_SIMILAR"]
]
df_completo = pd.merge(tecnicos, ultima[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]], on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# --- Filtros ---
with st.sidebar.expander("Filtros"):
    gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
    gerente = st.selectbox("👤 Filtrar por Gerente", gerentes)

    if gerente != "Todos":
        df_filtrado = df_completo[df_completo["GERENTE"] == gerente]
    else:
        df_filtrado = df_completo.copy()

    coordenadores = ["Todos"] + sorted(df_filtrado["COORDENADOR"].dropna().unique())
    coordenador = st.selectbox("👥 Filtrar por Coordenador", coordenadores)

    if coordenador != "Todos":
        df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador]

    status_options = ["OK", "PENDENTE", "SEM_INSPECAO"]
    status_selecionado = st.multiselect("📌 Filtrar por Status", status_options, default=status_options)

    df_filtrado = df_filtrado[df_filtrado["STATUS"].isin(status_selecionado)]

    # Filtro por data
    min_date = df["DATA_INSPECAO"].min()
    max_date = df["DATA_INSPECAO"].max()
    data_inicio, data_fim = st.date_input("📅 Filtrar por Data Inspeção", [min_date.date(), max_date.date()])

    df_filtrado = df_filtrado[
        (df_filtrado["DATA_INSPECAO"].fillna(pd.Timestamp.min) >= pd.Timestamp(data_inicio)) &
        (df_filtrado["DATA_INSPECAO"].fillna(pd.Timestamp.max) <= pd.Timestamp(data_fim))
    ]

# --- Indicadores ---
total = len(df_filtrado)
ok = (df_filtrado["STATUS"] == "OK").sum()
pend = (df_filtrado["STATUS"] == "PENDENTE").sum()
sem = (df_filtrado["STATUS"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

if page == "Visão Geral":
    col1, col2, col3 = st.columns(3)
    col1.metric("✔️ Técnicos OK", ok, f"{pct_ok} %", delta_color="normal")
    col2.metric("⚠️ Técnicos Pendentes", pend, f"{pct_pend} %", delta_color="inverse")
    col3.metric("❌ Técnicos Sem Inspeção", sem, f"{pct_sem} %", delta_color="normal")

    st.markdown("---")

    # Pizza geral
    pizza = df_filtrado["STATUS"].value_counts().reset_index()
    pizza.columns = ["STATUS", "QTD"]
    fig_pie = px.pie(pizza, names="STATUS", values="QTD",
                     color="STATUS",
                     color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
                     title="Distribuição Geral dos Status")
    st.plotly_chart(fig_pie, use_container_width=True)

if page == "Ranking por Coordenador":
    # Agrupando por coordenador
    grouped = df_filtrado.groupby("COORDENADOR")["STATUS"].value_counts().unstack(fill_value=0)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        if col not in grouped.columns:
            grouped[col] = 0
    ranking = grouped.reset_index()

    # Calcular % e gráfico barras empilhadas
    total_coord = ranking[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        ranking[col] = (ranking[col] / total_coord * 100).round(1)
    melted = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")

    fig_rank = px.bar(melted, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
                      barmode="stack", text_auto=True,
                      title="Distribuição (%) por Coordenador",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
    st.plotly_chart(fig_rank, use_container_width=True)

if page == "Ranking por Produto":
    grouped_prod = df_filtrado.groupby("PRODUTO_SIMILAR")["STATUS"].value_counts().unstack(fill_value=0)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        if col not in grouped_prod.columns:
            grouped_prod[col] = 0
    ranking_prod = grouped_prod.reset_index()

    total_prod = ranking_prod[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        ranking_prod[col] = (ranking_prod[col] / total_prod * 100).round(1)
    melted_prod = ranking_prod.melt(id_vars="PRODUTO_SIMILAR", var_name="STATUS", value_name="PERCENTUAL")

    fig_prod = px.bar(melted_prod, x="PRODUTO_SIMILAR", y="PERCENTUAL", color="STATUS",
                      barmode="stack", text_auto=True,
                      title="Distribuição (%) por Produto",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
    fig_prod.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_prod, use_container_width=True)

if page == "Dados Detalhados":
    st.markdown("### 📋 Tabela Detalhada")
    st.dataframe(df_filtrado)

    def gerar_excel(df):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
        buffer.seek(0)
        return buffer

    st.download_button("⬇️ Baixar Excel Filtrado", data=gerar_excel(df_filtrado),
                       file_name="painel_epi_filtrado.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
