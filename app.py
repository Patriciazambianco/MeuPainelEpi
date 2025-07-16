import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("🦺 Painel de Inspeções EPI")
st.markdown("---")

# 🚀 Lê do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# 🧼 Limpeza de colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# ✅ Corrige coluna STATUS com regra flexível
def mapear_status(valor):
    if "OK" in valor:
        return "OK"
    elif "PENDENTE" in valor:
        return "PENDENTE"
    else:
        return None

df["STATUS"] = df["STATUS_CHECK_LIST"].apply(mapear_status)

# 🎯 Última inspeção por técnico/produto
ultima_inspecao = (
    df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
)

# 🔗 Todos os técnicos + produtos possíveis
todos_pares = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"])[
    ["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]
]

# 🧩 Junta tudo
df_completo = pd.merge(
    todos_pares,
    ultima_inspecao[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)

df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# 💡 Classificação geral por técnico
def classificar(lista_status):
    status_set = set(lista_status)
    if status_set == {"OK"}:
        return "OK"
    elif status_set == {"SEM_INSPECAO"}:
        return "SEM_INSPECAO"
    else:
        return "PENDENTE"

status_tecnico = df_completo.groupby("TECNICO")["STATUS"].agg(list).reset_index()
status_tecnico["CLASSIFICACAO"] = status_tecnico["STATUS"].apply(classificar)

# Junta com COORDENADOR/GERENTE
df_class = pd.merge(
    status_tecnico,
    df_completo[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates(),
    on="TECNICO",
    how="left"
)

# 🎛️ Filtros no sidebar
with st.sidebar:
    st.header("🎛️ Filtros")
    gerente = st.selectbox("Filtrar por Gerente", ["Todos"] + sorted(df_class["GERENTE"].dropna().unique()))
    coordenador = st.selectbox("Filtrar por Coordenador", ["Todos"] + sorted(df_class["COORDENADOR"].dropna().unique()))
    status_sel = st.multiselect("Status", ["OK", "PENDENTE", "SEM_INSPECAO"], default=["OK", "PENDENTE", "SEM_INSPECAO"])

# Filtro aplicado
df_filt = df_class.copy()
if gerente != "Todos":
    df_filt = df_filt[df_filt["GERENTE"] == gerente]
if coordenador != "Todos":
    df_filt = df_filt[df_filt["COORDENADOR"] == coordenador]
df_filt = df_filt[df_filt["CLASSIFICACAO"].isin(status_sel)]

# 📊 Indicadores
total = len(df_filt)
ok = (df_filt["CLASSIFICACAO"] == "OK").sum()
pend = (df_filt["CLASSIFICACAO"] == "PENDENTE").sum()
sem = (df_filt["CLASSIFICACAO"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("✅ Técnicos 100% OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Com Pendências", pend, f"{pct_pend}%")
col3.metric("❌ Sem Inspeção", sem, f"{pct_sem}%")

# 🥧 Gráfico de Pizza
pizza = df_filt["CLASSIFICACAO"].value_counts().reindex(["OK", "PENDENTE", "SEM_INSPECAO"], fill_value=0).reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(
    pizza, names="STATUS", values="QTD", color="STATUS",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
    title="Distribuição dos Técnicos"
)
st.plotly_chart(fig_pie, use_container_width=True)

# 📊 Ranking por Coordenador com %
ranking = df_filt.groupby(["COORDENADOR", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

# Preenche colunas faltantes
for status in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if status not in ranking.columns:
        ranking[status] = 0

total_coord = ranking[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
for status in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    ranking[status] = (ranking[status] / total_coord * 100).round(1)

melted = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")
fig_bar = px.bar(
    melted, x="COORDENADOR", y="PERCENTUAL", color="STATUS", text="PERCENTUAL",
    barmode="stack", title="% Técnicos por Coordenador",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
fig_bar.update_traces(textposition="inside")
st.plotly_chart(fig_bar, use_container_width=True)

# 📥 Exporta Excel
def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    buffer.seek(0)
    return buffer

st.download_button("⬇️ Baixar Excel", gerar_excel(df_filt), file_name="painel_epi.xlsx")
