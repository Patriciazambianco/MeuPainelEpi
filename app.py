import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("🦺 Painel de Inspeções EPI")

# Link RAW do seu arquivo no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padroniza nomes das colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Padroniza STATUS_CHECK_LIST, transforma "CHECK LIST OK" em "OK"
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Última inspeção por técnico e produto
df_ult = (
    df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
)

# Lista completa técnico + produto + coordenador + gerente
todos_pares = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"])[
    ["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]
]

# Junta último status, preenche com SEM_INSPECAO quem não tem inspeção
df_completo = pd.merge(
    todos_pares,
    df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# Classificação do técnico considerando todos os produtos
def classifica_tecnico(status_list):
    status_set = set(status_list)
    if status_set == {"OK"}:
        return "OK"
    elif "PENDENTE" in status_set or "SEM_INSPECAO" in status_set:
        return "PENDENTE"
    else:
        return "PENDENTE"

status_tecnicos = df_completo.groupby("TECNICO")["STATUS"].apply(list).reset_index()
status_tecnicos["CLASSIFICACAO"] = status_tecnicos["STATUS"].apply(classifica_tecnico)

# Junta coordenador e gerente para cada técnico
meta = df_completo[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_final = pd.merge(status_tecnicos, meta, on="TECNICO", how="left")

# --- FILTROS ---
with st.sidebar:
    st.header("Filtros")
    gerentes = ["Todos"] + sorted(df_final["GERENTE"].dropna().unique())
    coordenadores = ["Todos"] + sorted(df_final["COORDENADOR"].dropna().unique())
    gerente_sel = st.selectbox("Gerente", gerentes)
    coordenador_sel = st.selectbox("Coordenador", coordenadores)
    status_sel = st.multiselect("Status", ["OK", "PENDENTE"], default=["OK", "PENDENTE"])

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

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos 100% OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Técnicos com Pendências (incluindo sem inspeção)", pend, f"{pct_pend}%")

# Gráfico pizza
pizza_df = df_filtrado["CLASSIFICACAO"].value_counts().reindex(["OK", "PENDENTE"], fill_value=0).reset_index()
pizza_df.columns = ["STATUS", "QTD"]
fig_pie = px.pie(
    pizza_df, names="STATUS", values="QTD", color="STATUS",
    color_discrete_map={"OK": "green", "PENDENTE": "red"},
    title="Distribuição dos Técnicos"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Ranking por coordenador (% técnicos)
ranking = df_filtrado.groupby(["COORDENADOR", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

for stts in ["OK", "PENDENTE"]:
    if stts not in ranking.columns:
        ranking[stts] = 0

ranking["TOTAL"] = ranking[["OK", "PENDENTE"]].sum(axis=1)

# Cálculo de % — divide cada status pelo total de técnicos daquele coordenador
for stts in ["OK", "PENDENTE"]:
    ranking[stts] = (ranking[stts] / ranking["TOTAL"] * 100).round(1)

ranking_melt = ranking.melt(id_vars="COORDENADOR", var_name="STATUS", value_name="PERCENTUAL")

fig_bar = px.bar(
    ranking_melt, x="COORDENADOR", y="PERCENTUAL", color="STATUS", text="PERCENTUAL",
    barmode="stack", title="% Técnicos por Coordenador",
    color_discrete_map={"OK": "green", "PENDENTE": "red"}
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
