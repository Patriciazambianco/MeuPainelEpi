import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Painel EPI", layout="wide")
st.title("💡 Painel de Inspeções EPI por Técnico")
st.markdown("---")

# Carrega dados do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normaliza colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Agrupa para pegar a última inspeção por técnico + produto
ultima = df.sort_values(["TECNICO", "DATA_INSPECAO"], ascending=[True, False])
ultima = ultima.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# Junta com todos os técnicos x produtos
todos = df.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"])[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]]
df_completo = pd.merge(todos, ultima[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]], on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM_INSPECAO")

# Agrupa por técnico para saber se está 100% OK ou não
def classificar_tecnico(status_list):
    if all(s == "OK" for s in status_list):
        return "OK"
    elif any(s == "PENDENTE" for s in status_list):
        return "PENDENTE"
    else:
        return "SEM_INSPECAO"

agrupado = df_completo.groupby("TECNICO")["STATUS"].agg(list).reset_index()
agrupado["CLASSIFICACAO"] = agrupado["STATUS"].apply(classificar_tecnico)

df_class = pd.merge(agrupado[["TECNICO", "CLASSIFICACAO"]],
                    df_completo[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates(),
                    on="TECNICO", how="left")

# Filtros
with st.sidebar:
    st.header("🔍 Filtros")
    gerente = st.selectbox("Filtrar por Gerente", ["Todos"] + sorted(df_class["GERENTE"].dropna().unique()))
    coordenador = st.selectbox("Filtrar por Coordenador", ["Todos"] + sorted(df_class["COORDENADOR"].dropna().unique()))
    status_sel = st.multiselect("Status", ["OK", "PENDENTE", "SEM_INSPECAO"], default=["OK", "PENDENTE", "SEM_INSPECAO"])

# Aplica filtros
df_filt = df_class.copy()
if gerente != "Todos":
    df_filt = df_filt[df_filt["GERENTE"] == gerente]
if coordenador != "Todos":
    df_filt = df_filt[df_filt["COORDENADOR"] == coordenador]
df_filt = df_filt[df_filt["CLASSIFICACAO"].isin(status_sel)]

# KPIs
total = len(df_filt)
ok = (df_filt["CLASSIFICACAO"] == "OK").sum()
pend = (df_filt["CLASSIFICACAO"] == "PENDENTE").sum()
sem = (df_filt["CLASSIFICACAO"] == "SEM_INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("✅ Técnicos 100% OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Técnicos com Pendência", pend, f"{pct_pend}%")
col3.metric("❌ Sem Inspeção", sem, f"{pct_sem}%")

# Gráfico pizza
pizza = df_filt["CLASSIFICACAO"].value_counts().reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(pizza, names="STATUS", values="QTD",
                 color="STATUS",
                 color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"},
                 title="Distribuição dos Técnicos por Status")
st.plotly_chart(fig_pie, use_container_width=True)

# Gráfico por coordenador
ranking = df_filt.groupby(["COORDENADOR", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

# Garante que todas as colunas existam
for col in ["OK", "PENDENTE", "SEM_INSPECAO"]:
    if col not in ranking.columns:
        ranking[col] = 0

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
    title="Técnicos por Coordenador (% 100% OK, Pendentes ou Sem Inspeção)",
    color_discrete_map={"OK": "green", "PENDENTE": "red", "SEM_INSPECAO": "gray"}
)
st.plotly_chart(fig_rank, use_container_width=True)

# Exportar Excel
def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Inspecoes")
    buffer.seek(0)
    return buffer

st.download_button("⬇️ Baixar Excel", gerar_excel(df_filt), file_name="inspecoes_tecnicos.xlsx")
