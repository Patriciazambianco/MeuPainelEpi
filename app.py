import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel Técnico - EPI", layout="wide")

# Título
title = "📊 Painel de Inspeções Técnicas - EPI 🛠️"
st.title(title)
st.markdown("### Monitoramento por Gerente, Coordenador e Produto - Status OK, Pendentes e Sem Inspeção")
st.markdown("---")

# Carregar Excel
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padronizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Última inspeção por técnico
ultima = df.sort_values(["TECNICO", "DATA_INSPECAO"], ascending=[True, False])
ultima = ultima.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# Técnicos com e sem inspeção
tecnicos = df[["TECNICO", "COORDENADOR", "GERENTE", "PRODUTO_SIMILAR"]].drop_duplicates()
df_completo = pd.merge(tecnicos, ultima[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]], on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# Filtros
gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
gerente = st.selectbox("👤 Filtrar por Gerente", gerentes)

filtrado = df_completo.copy()
if gerente != "Todos":
    filtrado = filtrado[filtrado["GERENTE"] == gerente]

coords = ["Todos"] + sorted(filtrado["COORDENADOR"].dropna().unique())
coordenador = st.selectbox("👥 Filtrar por Coordenador", coords)
if coordenador != "Todos":
    filtrado = filtrado[filtrado["COORDENADOR"] == coordenador]

status = st.multiselect("📌 Filtrar por Status", ["OK", "PENDENTE", "SEM_INSPECAO"], default=["OK", "PENDENTE", "SEM_INSPECAO"])
filtrado = filtrado[filtrado["STATUS"].isin(status)]

# Indicadores
total = len(filtrado)
ok = (filtrado["STATUS"] == "OK").sum()
pend = (filtrado["STATUS"] == "PENDENTE").sum()
sem = (filtrado["STATUS"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("✔️ Técnicos OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Pendentes", pend, f"{pct_pend}%")
col3.metric("❌ Sem Inspeção", sem, f"{pct_sem}%")

# Gráfico Pizza
pizza = filtrado["STATUS"].value_counts().reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(pizza, names="STATUS", values="QTD", title="Distribuição Geral",
                 color="STATUS",
                 color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
st.plotly_chart(fig_pie, use_container_width=True)

# Toggle
modo_percentual = st.toggle("📊 Mostrar gráfico como percentual", value=True)

# Gráfico Coordenador
group = df_completo.copy()
if gerente != "Todos":
    group = group[group["GERENTE"] == gerente]
if coordenador != "Todos":
    group = group[group["COORDENADOR"] == coordenador]

grouped = group.groupby("COORDENADOR")["STATUS"].value_counts().unstack(fill_value=0)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if col not in grouped.columns:
        grouped[col] = 0
ranking = grouped.reset_index()

if modo_percentual:
    total_coord = ranking[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        ranking[col] = (ranking[col] / total_coord * 100).round(1)
    melted = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")
    fig_rank = px.bar(melted, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
                      barmode="stack", text_auto=True,
                      title="Distribuição (%) por Coordenador",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
else:
    melted = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="QTD")
    fig_rank = px.bar(melted, x="COORDENADOR", y="QTD", color="STATUS",
                      barmode="group", text_auto=True,
                      title="Total por Coordenador",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
st.plotly_chart(fig_rank, use_container_width=True)

# Gráfico Produto
grouped_prod = group.groupby("PRODUTO_SIMILAR")["STATUS"].value_counts().unstack(fill_value=0)
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if col not in grouped_prod.columns:
        grouped_prod[col] = 0
ranking_prod = grouped_prod.reset_index()

if modo_percentual:
    total_prod = ranking_prod[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
    for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
        ranking_prod[col] = (ranking_prod[col] / total_prod * 100).round(1)
    melted_prod = ranking_prod.melt(id_vars="PRODUTO_SIMILAR", var_name="STATUS", value_name="PERCENTUAL")
    fig_prod = px.bar(melted_prod, x="PRODUTO_SIMILAR", y="PERCENTUAL", color="STATUS",
                      barmode="stack", text_auto=True,
                      title="Distribuição (%) por Produto",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
else:
    melted_prod = ranking_prod.melt(id_vars="PRODUTO_SIMILAR", var_name="STATUS", value_name="QTD")
    fig_prod = px.bar(melted_prod, x="PRODUTO_SIMILAR", y="QTD", color="STATUS",
                      barmode="group", text_auto=True,
                      title="Total por Produto",
                      color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"})
fig_prod.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_prod, use_container_width=True)

# Tabela e download
st.markdown("### 📋 Técnicos Filtrados")
st.dataframe(filtrado)

def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    buffer.seek(0)
    return buffer

st.download_button("⬇️ Baixar Excel Filtrado", data=gerar_excel(filtrado),
                   file_name="painel_epi_filtrado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
