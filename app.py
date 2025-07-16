import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("🦺 Painel de Inspeções EPI")
st.markdown("---")

# URL RAW do arquivo Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padroniza colunas para facilitar
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Mapear status OK/PENDENTE
def map_status(x):
    if "OK" in x:
        return "OK"
    elif "PENDENTE" in x:
        return "PENDENTE"
    else:
        return None

df["STATUS"] = df["STATUS_CHECK_LIST"].apply(map_status)

# Última inspeção por técnico + produto
ultima = (
    df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
)

# Lista completa técnico+produto com coordenador e gerente
todos_pares = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"])[
    ["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]
]

# Une com última inspeção (left join)
df_full = pd.merge(
    todos_pares,
    ultima[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)
df_full["STATUS"] = df_full["STATUS"].fillna("SEM_INSPECAO")

# Classifica cada técnico baseado nas inspeções dos produtos
def classifica_tecnico(lista):
    s = set(lista)
    if s == {"OK"}:
        return "OK"
    elif s == {"SEM_INSPECAO"}:
        return "SEM_INSPECAO"
    else:
        return "PENDENTE"

status_tec = df_full.groupby("TECNICO")["STATUS"].agg(list).reset_index()
status_tec["CLASSIFICACAO"] = status_tec["STATUS"].apply(classifica_tecnico)

# Junta coordenador e gerente (removendo duplicados)
meta = df_full[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_final = pd.merge(status_tec, meta, on="TECNICO", how="left")

# --- Filtros ---
with st.sidebar:
    st.header("Filtros")
    gerentes = ["Todos"] + sorted(df_final["GERENTE"].dropna().unique())
    coordenadores = ["Todos"] + sorted(df_final["COORDENADOR"].dropna().unique())
    gerente_sel = st.selectbox("Gerente", gerentes)
    coordenador_sel = st.selectbox("Coordenador", coordenadores)
    status_sel = st.multiselect("Status", ["OK", "PENDENTE", "SEM_INSPECAO"], default=["OK", "PENDENTE", "SEM_INSPECAO"])

df_filtered = df_final.copy()
if gerente_sel != "Todos":
    df_filtered = df_filtered[df_filtered["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtered = df_filtered[df_filtered["COORDENADOR"] == coordenador_sel]
df_filtered = df_filtered[df_filtered["CLASSIFICACAO"].isin(status_sel)]

# KPIs
total_tec = len(df_filtered)
ok_tec = (df_filtered["CLASSIFICACAO"] == "OK").sum()
pend_tec = (df_filtered["CLASSIFICACAO"] == "PENDENTE").sum()
sem_tec = (df_filtered["CLASSIFICACAO"] == "SEM_INSPECAO").sum()

pct_ok = round(ok_tec / total_tec * 100, 1) if total_tec else 0
pct_pend = round(pend_tec / total_tec * 100, 1) if total_tec else 0
pct_sem = round(sem_tec / total_tec * 100, 1) if total_tec else 0

col1, col2, col3 = st.columns(3)
col1.metric("✅ Técnicos 100% OK", ok_tec, f"{pct_ok}%")
col2.metric("⚠️ Técnicos com Pendências", pend_tec, f"{pct_pend}%")
col3.metric("❌ Técnicos sem Inspeção", sem_tec, f"{pct_sem}%")

# Gráfico pizza
pie_df = df_filtered["CLASSIFICACAO"].value_counts().reindex(["OK", "PENDENTE", "SEM_INSPECAO"], fill_value=0).reset_index()
pie_df.columns = ["STATUS", "QTD"]
fig_pie = px.pie(
    pie_df, names="STATUS", values="QTD", color="STATUS",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
    title="Distribuição dos Técnicos"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Ranking coordenador (%)
rank = df_filtered.groupby(["COORDENADOR", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

for status in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if status not in rank.columns:
        rank[status] = 0

rank["TOTAL"] = rank[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
for status in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    rank[status] = (rank[status] / rank["TOTAL"] * 100).round(1)

rank_melt = rank.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")

fig_bar = px.bar(
    rank_melt, x="COORDENADOR", y="PERCENTUAL", color="STATUS", text="PERCENTUAL",
    barmode="stack", title="% Técnicos por Coordenador",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
fig_bar.update_traces(textposition="inside")
st.plotly_chart(fig_bar, use_container_width=True)

# Botão download Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button("⬇️ Baixar Excel filtrado", to_excel(df_filtered), file_name="painel_epi_filtrado.xlsx")

