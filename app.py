import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# --- Carregar dados com cache ---
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
    df["PERSONALIZAR"] = df["PERSONALIZAR"].astype(str).str.strip().str.upper()
    df["PERSONALIZAR"] = df["PERSONALIZAR"].replace({
        "CHECK LIST OK": "OK",
        "PENDENTE": "PENDENTE"
    })
    return df

url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)

# --- Sidebar Filtros ---
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())
produtos = ["Todos"] + sorted(df["PRODUTO_SIMILAR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)
produto_sel = st.sidebar.selectbox("Produto", produtos)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]
if produto_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["PRODUTO_SIMILAR"] == produto_sel]

# =========================
# ======= MÉTRICAS ========
# =========================

# --- Cards gerais (baseados em linhas, como no seu original) ---
total_ok = (df_filtrado["PERSONALIZAR"]=="OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

# --- Técnicos sem saldo volante (por técnico único, não por linha) ---
# (qualquer valor não vazio conta como "tem saldo")
def serie_tem_saldo(s: pd.Series) -> bool:
    return (~(s.isna() | s.astype(str).str.strip().eq(""))).any()

g_tecnicos = df_filtrado.groupby("TECNICO").agg(
    pendente=("PERSONALIZAR", lambda s: (s == "PENDENTE").any()),
    tem_saldo=("SALDO_VOLANTE", serie_tem_saldo),
    gerente=("GERENTE", lambda s: s.dropna().iloc[0] if len(s.dropna()) else None),
    coordenador=("COORDENADOR", lambda s: s.dropna().iloc[0] if len(s.dropna()) else None)
)

tec_total = len(g_tecnicos)
tec_pend = int((g_tecnicos["pendente"] == True).sum())
tec_sem_saldo = int((g_tecnicos["tem_saldo"] == False).sum())
perc_sem_saldo_geral = (tec_sem_saldo / tec_total * 100) if tec_total > 0 else 0

# --- Dentro dos PENDENTES (por técnico único) ---
tec_pend_sem_saldo = int(((g_tecnicos["pendente"] == True) & (g_tecnicos["tem_saldo"] == False)).sum())
perc_pendentes = (tec_pend / tec_total * 100) if tec_total > 0 else 0
perc_pendentes_sem_saldo_dentro = (tec_pend_sem_saldo / tec_pend * 100) if tec_pend > 0 else 0

# --- Layout dos cards ---
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("✅ Técnicos OK (linhas)", total_ok)
c2.metric("📊 % OK (linhas)", f"{perc_ok:.1f}%")
c3.metric("⚠️ Pendentes (linhas)", total_pendente)
c4.metric("📊 % Pendentes (linhas)", f"{perc_pendente:.1f}%")
c5.metric("👤 Técnicos únicos", tec_total)
c6.metric("💸 Técnicos sem Saldo (únicos)", tec_sem_saldo)

d1, d2, d3 = st.columns(3)
d1.metric("🧑‍🔧 Técnicos Pendentes (únicos)", tec_pend)
d2.metric("📊 % Pendentes (únicos)", f"{perc_pendentes:.1f}%")
d3.metric("🎯 DENTRO dos Pendentes: % sem Saldo", f"{perc_pendentes_sem_saldo_dentro:.1f}%")

# =========================
# ======= GRÁFICOS ========
# =========================

# --- Gráfico por Gerente (base: contagem de técnicos únicos por status em cada gerente) ---
cont_ger = df_filtrado.groupby(["GERENTE","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_ger.columns:
        cont_ger[col] = 0
cont_ger["TOTAL"] = cont_ger["OK"] + cont_ger["PENDENTE"]
cont_ger["% OK"] = (cont_ger["OK"]/cont_ger["TOTAL"]*100).where(cont_ger["TOTAL"]>0, 0)
cont_ger["% PENDENTE"] = (cont_ger["PENDENTE"]/cont_ger["TOTAL"]*100).where(cont_ger["TOTAL"]>0, 0)

df_bar_ger = cont_ger.melt(id_vars=["GERENTE"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ","")

fig_ger = px.bar(
    df_bar_ger, x="GERENTE", y="PERCENTUAL", color="STATUS",
    barmode="group",
    text=df_bar_ger["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
    color_discrete_map={"OK":"green","PENDENTE":"red"},
    title="📊 Percentual de Técnicos OK vs Pendentes por Gerente (técnicos únicos)"
)
fig_ger.update_traces(textposition='outside')
fig_ger.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_ger, use_container_width=True)

# --- Gráfico por Coordenador ---
cont_coord = df_filtrado.groupby(["COORDENADOR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_coord.columns:
        cont_coord[col] = 0
cont_coord["TOTAL"] = cont_coord["OK"] + cont_coord["PENDENTE"]
cont_coord["% OK"] = (cont_coord["OK"]/cont_coord["TOTAL"]*100).where(cont_coord["TOTAL"]>0, 0)
cont_coord["% PENDENTE"] = (cont_coord["PENDENTE"]/cont_coord["TOTAL"]*100).where(cont_coord["TOTAL"]>0, 0)

df_bar_coord = cont_coord.melt(id_vars=["COORDENADOR"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ","")

fig_coord = px.bar(
    df_bar_coord, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
    barmode="group",
    text=df_bar_coord["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
    color_discrete_map={"OK":"green","PENDENTE":"red"},
    title="📊 Percentual de Técnicos OK vs Pendentes por Coordenador (técnicos únicos)"
)
fig_coord.update_traces(textposition='outside')
fig_coord.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_coord, use_container_width=True)

# --- Gráfico por Produto (Percentual de Pendências) ---
cont_prod = df_filtrado.groupby(["PRODUTO_SIMILAR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_prod.columns:
        cont_prod[col] = 0
cont_prod["TOTAL"] = cont_prod["OK"] + cont_prod["PENDENTE"]
cont_prod["% PENDENTE"] = (cont_prod["PENDENTE"]/cont_prod["TOTAL"]*100).where(cont_prod["TOTAL"]>0, 0)

fig_prod = px.bar(
    cont_prod, x="PRODUTO_SIMILAR", y="% PENDENTE",
    text=cont_prod["% PENDENTE"].apply(lambda x:f"{x:.1f}%"),
    color_discrete_sequence=["red"],
    title="📊 Percentual de Pendências por Produto (técnicos únicos)"
)
fig_prod.update_traces(textposition='outside')
fig_prod.update_layout(yaxis=dict(range=[0,110]))
st.plotly_chart(fig_prod, use_container_width=True)

# =========================
# ======= TABELAS =========
# =========================

# --- Tabela Pendentes (linhas) ---
df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes (linhas)")
st.dataframe(df_pendentes[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","PERSONALIZAR"]])

# --- Botão de Download genérico ---
def to_excel(df_export):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button(
    label="📥 Baixar Pendentes (Excel)",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Pendentes SEM saldo volante (por técnico único) ---
idx_pend_sem_saldo = g_tecnicos.index[(g_tecnicos["pendente"] == True) & (g_tecnicos["tem_saldo"] == False)]
df_pend_sem_saldo_tecnicos = (
    df_filtrado[df_filtrado["TECNICO"].isin(idx_pend_sem_saldo)]
    .sort_values(["GERENTE","COORDENADOR","TECNICO"])
)

st.markdown("### 💸 Técnicos Pendentes **sem** Saldo Volante (técnicos únicos)")
st.dataframe(
    df_pend_sem_saldo_tecnicos[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]]
        .drop_duplicates(subset=["TECNICO"])  # mostra 1 linha por técnico
)

st.download_button(
    label="📥 Baixar Pendentes sem Saldo (técnicos únicos)",
    data=to_excel(
        df_pend_sem_saldo_tecnicos[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]]
        .drop_duplicates(subset=["TECNICO"])
    ),
      file_name="epi_pendentes_sem_saldo_tecnicos.csv",
    mime="text/csv"
