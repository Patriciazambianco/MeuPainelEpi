import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("🦺 Painel de Inspeções EPI")

# Link direto RAW para o Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# Leitura e limpeza das colunas
df = pd.read_excel(url)
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Normaliza o status
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()

def map_status(x):
    if "OK" in x:
        return "OK"
    elif "PENDENTE" in x:
        return "PENDENTE"
    else:
        return None

df["STATUS"] = df["STATUS_CHECK_LIST"].apply(map_status)
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors='coerce')

# Pega a última inspeção por técnico + produto
df_ult = (
    df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
)

# Garante todos os pares técnico + produto com coordenador e gerente
todos_pares = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"])[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]]

# Une com última inspeção, preenchendo faltantes com SEM_INSPECAO
df_completo = pd.merge(
    todos_pares,
    df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# Classifica cada técnico:
def classifica_tecnico(lista_status):
    s = set(lista_status)
    if s == {"OK"}:
        return "OK"
    elif s == {"SEM_INSPECAO"}:
        return "SEM_INSPECAO"
    else:
        return "PENDENTE"

status_tec = df_completo.groupby("TECNICO")["STATUS"].agg(list).reset_index()
status_tec["CLASSIFICACAO"] = status_tec["STATUS"].apply(classifica_tecnico)

# Junta coordenador e gerente
meta = df_completo[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_final = pd.merge(status_tec, meta, on="TECNICO", how="left")

# --- Filtros ---
with st.sidebar:
    st.header("Filtros")
    gerentes = ["Todos"] + sorted(df_final["GERENTE"].dropna().unique())
    coordenadores = ["Todos"] + sorted(df_final["COORDENADOR"].dropna().unique())
    gerente_sel = st.selectbox("Gerente", gerentes)
    coordenador_sel = st.selectbox("Coordenador", coordenadores)
    status_sel = st.multiselect("Status", ["OK", "PENDENTE", "SEM_INSPECAO"], default=["OK", "PENDENTE", "SEM_INSPECAO"])

df_filtrado = df_final.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]
df_filtrado = df_filtrado[df_filtrado["CLASSIFICACAO"].isin(status_sel)]

# KPIs
total = len(df_filtrado)
ok = (df_filtrado["CLASSIFICACAO"] == "OK").sum()
pend = (df_filtrado["CLASSIFICACAO"] == "PENDENTE").sum()
sem = (df_filtrado["CLASSIFICACAO"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("✅ Técnicos 100% OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Técnicos com Pendências", pend, f"{pct_pend}%")
col3.metric("❌ Técnicos sem Inspeção", sem, f"{pct_sem}%")

# Gráfico pizza
pizza_df = df_filtrado["CLASSIFICACAO"].value_counts().reindex(["OK", "PENDENTE", "SEM_INSPECAO"], fill_value=0).reset_index()
pizza_df.columns = ["STATUS", "QTD"]
fig_pie = px.pie(
    pizza_df, names="STATUS", values="QTD", color="STATUS",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
    title="Distribuição dos Técnicos"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Ranking por coordenador (%)
ranking = df_filtrado.groupby(["COORDENADOR", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

for stts in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if stts not in ranking.columns:
        ranking[stts] = 0

ranking["TOTAL"] = ranking[["OK", "PENDENTE", "SEM_INSPECAO"]].sum(axis=1)
for stts in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    ranking[stts] = (ranking[stts] / ranking["TOTAL"] * 100).round(1)

ranking_melt = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")
fig_bar = px.bar(
    ranking_melt, x="COORDENADOR", y="PERCENTUAL", color="STATUS", text="PERCENTUAL",
    barmode="stack", title="% Técnicos por Coordenador",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
fig_bar.update_traces(textposition="inside")
st.plotly_chart(fig_bar, use_container_width=True)

# Botão para baixar Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button("⬇️ Baixar Excel filtrado", to_excel(df_filtrado), file_name="painel_epi_filtrado.xlsx")
