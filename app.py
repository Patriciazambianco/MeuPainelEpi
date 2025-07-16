import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- Página ---
st.set_page_config(page_title="Painel EPI", layout="wide")

st.title("🛠️ Painel Técnico - Inspeções EPI")
st.markdown("---")

# --- Carrega dados do GitHub ---
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# --- Normaliza colunas ---
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

# Técnicos com e sem inspeção
tecnicos = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="last")[
    ["TECNICO", "COORDENADOR", "GERENTE", "PRODUTO_SIMILAR"]
]
df_completo = pd.merge(
    tecnicos,
    ultima[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# --- Filtros ---
with st.sidebar:
    st.header("🔍 Filtros")

    gerente = st.selectbox("Filtrar por Gerente", ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique()))
    coordenador = st.selectbox("Filtrar por Coordenador", ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique()))
    status_options = ["OK", "PENDENTE", "SEM_INSPECAO"]
    status_selecionado = st.multiselect("Status", status_options, default=status_options)

# Aplica filtros
df_filtrado = df_completo.copy()
if gerente != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente]
if coordenador != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador]
df_filtrado = df_filtrado[df_filtrado["STATUS"].isin(status_selecionado)]

# --- KPIs ---
total = len(df_filtrado)
ok = (df_filtrado["STATUS"] == "OK").sum()
pend = (df_filtrado["STATUS"] == "PENDENTE").sum()
sem = (df_filtrado["STATUS"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("✔️ Técnicos OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Técnicos Pendentes", pend, f"{pct_pend}%")
col3.metric("❌ Sem Inspeção", sem, f"{pct_sem}%")

# --- Pizza geral ---
st.markdown("### 📊 Distribuição Geral")
pizza = df_filtrado["STATUS"].value_counts().reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(pizza, names="STATUS", values="QTD",
                 color="STATUS",
                 color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
                 title="Distribuição dos Status")
st.plotly_chart(fig_pie, use_container_width=True)

# --- Ranking por Coordenador ---
st.markdown("### 📈 Ranking por Coordenador (%)")

grouped = df_filtrado.groupby("COORDENADOR")["STATUS"].value_counts().unstack(fill_value=0)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if col not in grouped.columns:
        grouped[col] = 0
ranking = grouped.reset_index()

total_coord = ranking[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    ranking[col] = (ranking[col] / total_coord * 100).round(1)
melted = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")

fig_rank = px.bar(
    melted,
    x="COORDENADOR",
    y="PERCENTUAL",
    color="STATUS",
    barmode="stack",
    text_auto=True,
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
st.plotly_chart(fig_rank, use_container_width=True)

# --- Ranking por Produto ---
st.markdown("### 🧰 Ranking por Produto (%)")
grouped_prod = df_filtrado.groupby("PRODUTO_SIMILAR")["STATUS"].value_counts().unstack(fill_value=0)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if col not in grouped_prod.columns:
        grouped_prod[col] = 0
ranking_prod = grouped_prod.reset_index()

total_prod = ranking_prod[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    ranking_prod[col] = (ranking_prod[col] / total_prod * 100).round(1)
melted_prod = ranking_prod.melt(id_vars="PRODUTO_SIMILAR", var_name="STATUS", value_name="PERCENTUAL")

fig_prod = px.bar(
    melted_prod,
    x="PRODUTO_SIMILAR",
    y="PERCENTUAL",
    color="STATUS",
    barmode="stack",
    text_auto=True,
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
fig_prod.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_prod, use_container_width=True)

# --- Tabela detalhada ---
st.markdown("### 📋 Tabela com Técnicos e Inspeções")
st.dataframe(df_filtrado)

# --- Exportar Excel ---
def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Inspeções")
    buffer.seek(0)
    return buffer

st.download_button(
    "⬇️ Baixar Excel",
    data=gerar_excel(df_filtrado),
    file_name="inspecoes_epi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
