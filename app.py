import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# Carregar dados
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normalizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["PERSONALIZAR"] = df["PERSONALIZAR"].astype(str).str.strip().str.upper()

# Filtros
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"]==gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"]==coordenador_sel]

# --- Cards gerais ---
total_ok = (df_filtrado["PERSONALIZAR"]=="CHECK LIST OK").sum()
total_pendente = (df_filtrado["PERSONALIZAR"]=="PENDENTE").sum()
total_geral = total_ok + total_pendente
perc_ok = total_ok/total_geral*100 if total_geral>0 else 0
perc_pendente = total_pendente/total_geral*100 if total_geral>0 else 0

col1,col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# --- Gráfico por gerente ---
contagem_ger = df_filtrado.groupby(["GERENTE","PERSONALIZAR"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["CHECK LIST OK","PENDENTE"]:
    if col not in contagem_ger.columns:
        contagem_ger[col]=0
contagem_ger["TOTAL"]=contagem_ger["CHECK LIST OK"]+contagem_ger["PENDENTE"]
contagem_ger["% OK"] = contagem_ger["CHECK LIST OK"]/contagem_ger["TOTAL"]*100
contagem_ger["% PENDENTE"] = contagem_ger["PENDENTE"]/contagem_ger["TOTAL"]*100

df_bar_ger = contagem_ger.melt(id_vars=["GERENTE"], value_vars=["% OK","% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ","").str.capitalize()

fig = px.bar(df_bar_ger, x="GERENTE", y="PERCENTUAL", color="STATUS",
             barmode="group", text=df_bar_ger["PERCENTUAL"].apply(lambda x:f"{x:.1f}%"),
             color_discrete_map={"Ok":"green","Pendente":"red"},
             title="📊 Percentual de Técnicos OK vs Pendentes por Gerente")
fig.update_traces(textposition='outside')
fig.update_layout(yaxis=dict(range=[0,110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig,use_container_width=True)

# --- Tabela pendentes ---
df_pendentes = df_filtrado[df_filtrado["PERSONALIZAR"]=="PENDENTE"]
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO","COORDENADOR","GERENTE","PERSONALIZAR"]])
