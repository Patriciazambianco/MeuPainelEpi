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

# --- Cards gerais ---
total_ok = (df_filtrado["PERSONALIZAR"]=="OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ Técnicos OK", total_ok)
c2.metric("📊 % OK", f"{perc_ok:.1f}%")
c3.metric("⚠️ Pendentes", total_pendente)
c4.metric("📊 % Pendentes", f"{perc_pendente:.1f}%")

# --- Gráfico por Gerente ---
cont_ger = df_filtrado.groupby(["GERENTE","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_ger.columns:
        cont_ger[col]=0
cont_ger["TOTAL"] = cont_ger["OK"]+cont_ger["PENDENTE"]
cont_ger["% OK"] = (cont_ger["OK"]/cont_ger["TOTAL"]*100).where(cont_ger["TOTAL"]>0,0)
cont_ger["% PENDENTE"] = (cont_ger["PENDENTE"]/cont_ger["TOTAL"]*100).where(cont_ger["TOTAL"]>0,0)

df_bar_ger = cont_ger.melt(id_vars=["GERENTE"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ","")

fig_ger = px.bar(df_bar_ger, x="GERENTE", y="PERCENTUAL", color="STATUS",
             barmode="group", text=df_bar_ger["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
             color_discrete_map={"OK":"green","PENDENTE":"red"},
             title="📊 Percentual de Técnicos OK vs Pendentes por Gerente")
fig_ger.update_traces(textposition='outside')
fig_ger.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_ger,use_container_width=True)

# --- Gráfico por Coordenador ---
cont_coord = df_filtrado.groupby(["COORDENADOR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_coord.columns:
        cont_coord[col]=0
cont_coord["TOTAL"] = cont_coord["OK"]+cont_coord["PENDENTE"]
cont_coord["% OK"] = (cont_coord["OK"]/cont_coord["TOTAL"]*100).where(cont_coord["TOTAL"]>0,0)
cont_coord["% PENDENTE"] = (cont_coord["PENDENTE"]/cont_coord["TOTAL"]*100).where(cont_coord["TOTAL"]>0,0)

df_bar_coord = cont_coord.melt(id_vars=["COORDENADOR"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ","")

fig_coord = px.bar(df_bar_coord, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
             barmode="group", text=df_bar_coord["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
             color_discrete_map={"OK":"green","PENDENTE":"red"},
             title="📊 Percentual de Técnicos OK vs Pendentes por Coordenador")
fig_coord.update_traces(textposition='outside')
fig_coord.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_coord,use_container_width=True)

# --- Gráfico por Produto (Percentual de Pendências) ---
cont_prod = df_filtrado.groupby(["PRODUTO_SIMILAR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK","PENDENTE"]:
    if col not in cont_prod.columns:
        cont_prod[col]=0
cont_prod["TOTAL"] = cont_prod["OK"]+cont_prod["PENDENTE"]
cont_prod["% PENDENTE"] = (cont_prod["PENDENTE"]/cont_prod["TOTAL"]*100).where(cont_prod["TOTAL"]>0,0)

fig_prod = px.bar(cont_prod, x="PRODUTO_SIMILAR", y="% PENDENTE",
                  text=cont_prod["% PENDENTE"].apply(lambda x:f"{x:.1f}%"),
                  color_discrete_sequence=["red"],
                  title="📊 Percentual de Pendências por Produto")
fig_prod.update_traces(textposition='outside')
fig_prod.update_layout(yaxis=dict(range=[0,110]))
st.plotly_chart(fig_prod,use_container_width=True)

# --- Tabela Pendentes ---
df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","PERSONALIZAR"]])

# --- Botão de Download Pendentes ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button(
    label="📥 Baixar Pendentes (Excel)",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Técnicos sem saldo volante ---
df_sem_saldo = df_filtrado[df_filtrado["SALDO_VOLANTE"].isna() | (df_filtrado["SALDO_VOLANTE"].astype(str).str.strip() == "")]
st.markdown("### 💸 Técnicos sem Saldo Volante")
st.dataframe(df_sem_saldo[["TECNICO","PRODUTO_SIMILAR","COORDENADOR","GERENTE","SALDO_VOLANTE"]])

st.download_button(
    label="📥 Baixar Técnicos sem Saldo Volante (Excel)",
    data=to_excel(df_sem_saldo),
    file_name="epi_tecnicos_sem_saldo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
