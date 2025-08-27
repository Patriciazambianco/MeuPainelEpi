import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")


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


# Cards baseados em linhas
total_ok = (df_filtrado["PERSONALIZAR"]=="OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

# Técnicos únicos
def tem_saldo(s: pd.Series) -> bool:
    return (~(s.isna() | s.astype(str).str.strip().eq(""))).any()

g_tecnicos = df_filtrado.groupby("TECNICO").agg(
    pendente=("PERSONALIZAR", lambda s: (s == "PENDENTE").any()),
    tem_saldo=("SALDO_VOLANTE", tem_saldo),
    gerente=("GERENTE", lambda s: s.dropna().iloc[0] if len(s.dropna()) else None),
    coordenador=("COORDENADOR", lambda s: s.dropna().iloc[0] if len(s.dropna()) else None)
)

tec_total = len(g_tecnicos)
tec_pend = int((g_tecnicos["pendente"] == True).sum())
tec_sem_saldo = int((g_tecnicos["tem_saldo"] == False).sum())
tec_pend_sem_saldo = int(((g_tecnicos["pendente"] == True) & (g_tecnicos["tem_saldo"] == False)).sum())

perc_pendentes = (tec_pend / tec_total * 100) if tec_total > 0 else 0
perc_pendentes_sem_saldo = (tec_pend_sem_saldo / tec_pend * 100) if tec_pend > 0 else 0

# --- Layout dos cards ---
c1, c2, c3, c4, c5, c6 = st.columns(6)
c2.metric("📊 % OK", f"{perc_ok:.1f}%")
c4.metric("📊 % Pendentes", f"{perc_pendente:.1f}%")
c6.metric("💸 Técnicos sem Saldo (únicos)", tec_sem_saldo)

d1, d2, d3 = st.columns(3)
d1.metric("🧑‍🔧 Técnicos Pendentes (únicos)", tec_pend)
d2.metric("📊 % Pendentes (únicos)", f"{perc_pendentes:.1f}%")
d3.metric("🎯 DENTRO dos Pendentes: % sem Saldo", f"{perc_pendentes_sem_saldo:.1f}%")

# =========================
# ======= GRÁFICOS ========
# =========================

def criar_grafico(df_filtrado, eixo, titulo):
    cont = df_filtrado.groupby([eixo,"PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
    for col in ["OK","PENDENTE"]:
        if col not in cont.columns:
            cont[col] = 0
    cont["TOTAL"] = cont["OK"] + cont["PENDENTE"]
    cont["% OK"] = (cont["OK"]/cont["TOTAL"]*100).where(cont["TOTAL"]>0, 0)
    cont["% PENDENTE"] = (cont["PENDENTE"]/cont["TOTAL"]*100).where(cont["TOTAL"]>0, 0)
    df_bar = cont.melt(id_vars=[eixo], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
    df_bar["STATUS"] = df_bar["STATUS"].str.replace("% ","")
    fig = px.bar(
        df_bar, x=eixo, y="PERCENTUAL", color="STATUS",
        barmode="group",
        text=df_bar["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
        color_discrete_map={"OK":"green","PENDENTE":"red"},
        title=titulo
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig,use_container_width=True)

criar_grafico(df_filtrado, "GERENTE", "📊 Percentual de Técnicos OK vs Pendentes por Gerente (técnicos únicos)")
criar_grafico(df_filtrado, "COORDENADOR", "📊 Percentual de Técnicos OK vs Pendentes por Coordenador (técnicos únicos)")
criar_grafico(df_filtrado, "PRODUTO_SIMILAR", "📊 Percentual de Pendências por Produto (técnicos únicos)")

# =========================
# ======= TABELAS =========
# =========================

# Tabela pendentes (linhas)
df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes (linhas)")
st.dataframe(df_pendentes[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","PERSONALIZAR"]])

# Botão download pendentes
def to_excel(df_export):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

st.download_button(
    label="📥 Baixar Pendentes (Excel)",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Pendentes sem saldo volante (técnicos únicos)
idx_pend_sem_saldo = g_tecnicos.index[(g_tecnicos["pendente"] == True) & (g_tecnicos["tem_saldo"] == False)]
df_pend_sem_saldo_tecnicos = df_filtrado[df_filtrado["TECNICO"].isin(idx_pend_sem_saldo)]
df_pend_sem_saldo_tecnicos = df_pend_sem_saldo_tecnicos.drop_duplicates(subset=["TECNICO"]).sort_values(["GERENTE","COORDENADOR","TECNICO"])

st.markdown("### 💸 Técnicos Pendentes **sem** Saldo Volante (técnicos únicos)")
st.dataframe(df_pend_sem_saldo_tecnicos[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]])

st.download_button(
    label="📥 Baixar Pendentes sem Saldo (técnicos únicos)",
    data=to_excel(df_pend_sem_saldo_tecnicos[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]]),
    file_name="epi_pendentes_sem_saldo_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
