import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# =============================
# Configuração da página
# =============================
st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# =============================
# Carregar dados do GitHub
# =============================
@st.cache_data
def carregar_dados():
    url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url)
    return df

df = carregar_dados()

# =============================
# Normalizar colunas e status
# =============================
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.strip().str.upper()
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
df["STATUS"] = df["STATUS_CHECK_LIST"].apply(lambda x: "OK" if x == "CHECK LIST OK" else "PENDENTE")

# =============================
# Sidebar - Filtros
# =============================
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

# =============================
# Criar tabela completa de técnicos
# =============================
# Todos os técnicos
todos_tecnicos = df_filtrado[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Última inspeção por técnico (status)
df_ult = (
    df_filtrado.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO"], keep="first")[["TECNICO", "STATUS", "DATA_INSPECAO"]]
)

# Combinar todos os técnicos com a última inspeção
df_completo = pd.merge(todos_tecnicos, df_ult, on="TECNICO", how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")
df_completo["DATA_INSPECAO"] = pd.to_datetime(df_completo["DATA_INSPECAO"])

# =============================
# Contagem por coordenador
# =============================
contagem_coord = df_completo.groupby(["COORDENADOR", "STATUS"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
for col in ["OK", "PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col] = 0
contagem_coord["TOTAL"] = contagem_coord["OK"] + contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"] / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"] / contagem_coord["TOTAL"]) * 100

# =============================
# Cards de indicadores gerais
# =============================
total_ok = contagem_coord["OK"].sum()
total_pendente = contagem_coord["PENDENTE"].sum()
total_geral = total_ok + total_pendente
perc_ok = (total_ok / total_geral * 100) if total_geral > 0 else 0
perc_pendente = (total_pendente / total_geral * 100) if total_geral > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# =============================
# Gráfico de pizza
# =============================
fig_pizza = px.pie(
    names=["OK", "Pendentes"],
    values=[total_ok, total_pendente],
    color_discrete_map={"OK": "green", "Pendentes": "red"},
    hole=0.4
)
fig_pizza.update_traces(textinfo="percent+label")
st.plotly_chart(fig_pizza, use_container_width=True)

# =============================
# Gráfico de barras agrupadas por coordenador (%)
# =============================
df_bar = contagem_coord.melt(
    id_vars=["COORDENADOR"],
    value_vars=["% OK", "% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)
df_bar["STATUS"] = df_bar["STATUS"].str.replace("% ", "").str.capitalize()

fig_bar = px.bar(
    df_bar,
    x="COORDENADOR",
    y="PERCENTUAL",
    color="STATUS",
    barmode="group",
    text=df_bar["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
    color_discrete_map={"Ok": "green", "Pendente": "red"},
    title="📊 Percentual de Técnicos OK vs Pendentes por Coordenador"
)
fig_bar.update_traces(textposition='outside')
fig_bar.update_layout(yaxis=dict(range=[0, 110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_bar, use_container_width=True)

# =============================
# Download de Pendentes
# =============================
df_pendentes = df_completo[df_completo["STATUS"] == "PENDENTE"]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    return output.getvalue()

if not df_pendentes.empty:
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=to_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================
# Tabelas de Percentual e Pendentes
# =============================
st.markdown("### 📊 Percentual de Técnicos por Coordenador")
st.dataframe(contagem_coord[["COORDENADOR", "TOTAL", "OK", "PENDENTE", "% OK", "% PENDENTE"]])

st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "DATA_INSPECAO", "STATUS"]])
