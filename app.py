import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("🦺 Painel de Inspeções EPI - Status Técnico (100% OK ou Pendentes)")

# Link RAW do seu arquivo no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normaliza nomes das colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Padroniza STATUS_CHECK_LIST para OK/PENDENTE
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Todos técnicos e todos produtos possíveis (garante incluir técnicos sem inspeção em produtos)
todos_tecnicos = df["TECNICO"].dropna().unique()
todos_produtos = df["PRODUTO_SIMILAR"].dropna().unique()

# Cria produto x técnico "completo" pra garantir todas combinações
todos_pares = pd.MultiIndex.from_product([todos_tecnicos, todos_produtos], names=["TECNICO", "PRODUTO_SIMILAR"]).to_frame(index=False)

# Junta com coordenador e gerente (puxa do df original, usando drop_duplicates para garantir relação)
relacoes = df[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates(subset=["TECNICO"])
todos_pares = pd.merge(todos_pares, relacoes, on="TECNICO", how="left")

# Última inspeção por técnico + produto
df_ult = (
    df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
    [["TECNICO", "PRODUTO_SIMILAR", "STATUS"]]
)

# Junta os status com o completo (garante que técnicos sem inspeção terão NaN)
df_completo = pd.merge(todos_pares, df_ult, on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

# Substitui NaN por SEM_INSPECAO
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# Função para classificar técnico: só OK se TODOS os status dele forem OK
def classifica_tecnico(status_list):
    if all(s == "OK" for s in status_list):
        return "OK"
    else:
        return "PENDENTE"

# Agrupa por técnico, cria lista dos status
status_por_tecnico = df_completo.groupby("TECNICO")["STATUS"].apply(list).reset_index()
status_por_tecnico["CLASSIFICACAO"] = status_por_tecnico["STATUS"].apply(classifica_tecnico)

# Junta coordenador e gerente pra cada técnico
meta = df_completo[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_final = pd.merge(status_por_tecnico, meta, on="TECNICO", how="left")

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

# Download Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button("⬇️ Baixar Excel filtrado", to_excel(df_filtrado), file_name="painel_epi_filtrado.xlsx")
