import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# Carregar dados
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normalizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["PERSONALIZAR"] = df["PERSONALIZAR"].astype(str).str.strip().str.upper()

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
total_ok = (df_filtrado["PERSONALIZAR"]=="CHECK LIST OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

col1,col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# --- Gráfico por Gerente ---
cont_ger = df_filtrado.groupby(["GERENTE","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["CHECK LIST OK","PENDENTE"]:
    if col not in cont_ger.columns:
        cont_ger[col]=0
cont_ger["TOTAL"]=cont_ger["CHECK LIST OK"]+cont_ger["PENDENTE"]
cont_ger["% OK"]=cont_ger["CHECK LIST OK"]/cont_ger["TOTAL"]*100
cont_ger["% PENDENTE"]=cont_ger["PENDENTE"]/cont_ger["TOTAL"]*100

df_bar_ger = cont_ger.melt(id_vars=["GERENTE"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_ger["STATUS"]=df_bar_ger["STATUS"].str.replace("% ","").str.capitalize()

fig_ger = px.bar(df_bar_ger, x="GERENTE", y="PERCENTUAL", color="STATUS",
             barmode="group", text=df_bar_ger["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
             color_discrete_map={"Ok":"green","Pendente":"red"},
             title="📊 Percentual de Técnicos OK vs Pendentes por Gerente")
fig_ger.update_traces(textposition='outside')
fig_ger.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_ger,use_container_width=True)

# --- Gráfico por Coordenador ---
cont_coord = df_filtrado.groupby(["COORDENADOR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["CHECK LIST OK","PENDENTE"]:
    if col not in cont_coord.columns:
        cont_coord[col]=0
cont_coord["TOTAL"]=cont_coord["CHECK LIST OK"]+cont_coord["PENDENTE"]
cont_coord["% OK"]=cont_coord["CHECK LIST OK"]/cont_coord["TOTAL"]*100
cont_coord["% PENDENTE"]=cont_coord["PENDENTE"]/cont_coord["TOTAL"]*100

df_bar_coord = cont_coord.melt(id_vars=["COORDENADOR"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_coord["STATUS"]=df_bar_coord["STATUS"].str.replace("% ","").str.capitalize()

fig_coord = px.bar(df_bar_coord, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
             barmode="group", text=df_bar_coord["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
             color_discrete_map={"Ok":"green","Pendente":"red"},
             title="📊 Percentual de Técnicos OK vs Pendentes por Coordenador")
fig_coord.update_traces(textposition='outside')
fig_coord.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_coord,use_container_width=True)

# --- Gráfico por Produto (Percentual de Pendências) ---
cont_prod = df_filtrado.groupby(["PRODUTO_SIMILAR","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["CHECK LIST OK","PENDENTE"]:
    if col not in cont_prod.columns:
        cont_prod[col]=0
cont_prod["TOTAL"]=cont_prod["CHECK LIST OK"]+cont_prod["PENDENTE"]
cont_prod["% PENDENTE"]=cont_prod["PENDENTE"]/cont_prod["TOTAL"]*100

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

# --- Botão de Download ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

st.download_button(
    label="📥 Baixar Pendentes (Excel)",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
