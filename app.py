import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

@st.cache_data
def carregar_dados():
    url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url)
    return df

df = carregar_dados()

# Normalizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.strip().str.upper()
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
df["STATUS"] = df["STATUS_CHECK_LIST"].apply(lambda x: "OK" if x=="CHECK LIST OK" else "PENDENTE")

# Sidebar - filtros
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# --- Criar tabela completa técnico + produto ---
todos_tecnicos_prod = df_filtrado[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE"]].drop_duplicates()
df_status_prod = pd.merge(
    todos_tecnicos_prod,
    df_filtrado[["TECNICO","PRODUTO_SIMILAR","STATUS"]],
    on=["TECNICO","PRODUTO_SIMILAR"],
    how="left"
)
df_status_prod["STATUS"] = df_status_prod["STATUS"].fillna("PENDENTE")

# --- Agregação por técnico ---
def status_tecnico(grupo):
    if all(s=="OK" for s in grupo):
        return "OK"
    else:
        return "PENDENTE"

df_status_tecnico = df_status_prod.groupby(["TECNICO","COORDENADOR","GERENTE"])["STATUS"].apply(status_tecnico).reset_index()

# -------------------------
# Contagem e % por coordenador
# -------------------------
contagem_coord = df_status_tecnico.groupby(["COORDENADOR","STATUS"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col]=0
contagem_coord["TOTAL"]=contagem_coord["OK"]+contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"]/contagem_coord["TOTAL"]*100)
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"]/contagem_coord["TOTAL"]*100)

# -------------------------
# Contagem e % por gerente
# -------------------------
contagem_ger = df_status_tecnico.groupby(["GERENTE","STATUS"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in contagem_ger.columns:
        contagem_ger[col]=0
contagem_ger["TOTAL"]=contagem_ger["OK"]+contagem_ger["PENDENTE"]
contagem_ger["% OK"] = (contagem_ger["OK"]/contagem_ger["TOTAL"]*100)
contagem_ger["% PENDENTE"] = (contagem_ger["PENDENTE"]/contagem_ger["TOTAL"]*100)

# -------------------------
# Cards gerais
# -------------------------
total_ok = df_status_tecnico[df_status_tecnico["STATUS"]=="OK"].shape[0]
total_pendente = df_status_tecnico[df_status_tecnico["STATUS"]=="PENDENTE"].shape[0]
total_geral = total_ok + total_pendente
perc_ok = (total_ok/total_geral*100) if total_geral>0 else 0
perc_pendente = (total_pendente/total_geral*100) if total_geral>0 else 0

col1,col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# -------------------------
# Gráfico coordenador
# -------------------------
df_bar_coord = contagem_coord.melt(
    id_vars=["COORDENADOR"],
    value_vars=["% OK","% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)
df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ","").str.capitalize()
fig_bar_coord = px.bar(
    df_bar_coord,
    x="COORDENADOR",
    y="PERCENTUAL",
    color="STATUS",
    barmode="group",
    text=df_bar_coord["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
    color_discrete_map={"Ok":"green","Pendente":"red"},
    title="📊 Percentual de Técnicos OK vs Pendentes por Coordenador"
)
fig_bar_coord.update_traces(textposition='outside')
fig_bar_coord.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_bar_coord,use_container_width=True)

# -------------------------
# Gráfico gerente
# -------------------------
df_bar_ger = contagem_ger.melt(
    id_vars=["GERENTE"],
    value_vars=["% OK","% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)
df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ","").str.capitalize()
fig_bar_ger = px.bar(
    df_bar_ger,
    x="GERENTE",
    y="PERCENTUAL",
    color="STATUS",
    barmode="group",
    text=df_bar_ger["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
    color_discrete_map={"Ok":"green","Pendente":"red"},
    title="📊 Percentual de Técnicos OK vs Pendentes por Gerente"
)
fig_bar_ger.update_traces(textposition='outside')
fig_bar_ger.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_bar_ger,use_container_width=True)

# -------------------------
# Tabela pendentes
# -------------------------
df_pendentes = df_status_tecnico[df_status_tecnico["STATUS"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO","COORDENADOR","GERENTE","STATUS"]])
