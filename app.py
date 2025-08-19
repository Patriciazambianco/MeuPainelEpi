import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta

# Configurações iniciais
st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.markdown("<h1 style='text-align:center;'>🦺 Painel de Inspeções EPI</h1>", unsafe_allow_html=True)

# --- 📥 Carregar dados com cache ---
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%83O%20EPI.xlsx"
    return pd.read_excel(url)

df = carregar_dados()

# Padronizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()

# Converter datas
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Obter todos técnico + produto (garantir quem não tem inspeção)
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Obter última inspeção real
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
    .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
    .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
    [["TECNICO", "PRODUTO_SIMILAR", "STATUS_CHECK_LIST", "DATA_INSPECAO"]]
)

# Juntar com todos técnicos+produtos (para garantir presença de quem nunca teve inspeção)
df_completo = pd.merge(
    tecnicos_produtos,
    df_ult,
    on=["TECNICO", "PRODUTO_SIMILAR"],
    how="left"
)

# --- 🟢🔴 Regras de STATUS ---
hoje = datetime.today()
limite = hoje - timedelta(days=180)

def definir_status(row):
    if pd.isna(row["DATA_INSPECAO"]):
        return "PENDENTE"
    elif row["DATA_INSPECAO"] < limite:
        return "PENDENTE"
    elif str(row["STATUS_CHECK_LIST"]).strip().upper() == "CHECK LIST OK":
        return "OK"
    else:
        return "PENDENTE"

df_completo["STATUS"] = df_completo.apply(definir_status, axis=1)

# Sidebar - Filtros
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_filtrado = df_completo.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# Contagem por coordenador
contagem_coord = df_filtrado.groupby(["COORDENADOR", "STATUS"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()

# Garantir colunas sempre existentes
for col in ["OK", "PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col] = 0

# Criar totais e percentuais
contagem_coord["TOTAL"] = contagem_coord["OK"] + contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"] / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"] / contagem_coord["TOTAL"]) * 100

# --- 🔁 CARDS ---
total_ok = contagem_coord["OK"].sum()
total_pendente = contagem_coord["PENDENTE"].sum()
total_geral = total_ok + total_pendente
perc_ok = (total_ok / total_geral) * 100 if total_geral > 0 else 0
perc_pendente = (total_pendente / total_geral) * 100 if total_geral > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# --- 📊 GRÁFICO ---
df_grafico = contagem_coord.melt(
    id_vars=["COORDENADOR"],
    value_vars=["% OK", "% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)
df_grafico["STATUS"] = df_grafico["STATUS"].str.replace("% ", "").str.capitalize()

fig = px.bar(
    df_grafico,
    x="COORDENADOR",
    y="PERCENTUAL",
    color="STATUS",
    barmode="group",
    text=df_grafico["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
    color_discrete_map={"Ok": "green", "Pendente": "red"},
    title="📊 Percentual de Técnicos OK e Pendentes por Coordenador"
)
fig.update_traces(textposition='outside')
fig.update_layout(yaxis=dict(range=[0, 110]), uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig, use_container_width=True)

# --- 📥 BOTÃO DE DOWNLOAD REAL (estilizado) ---
df_pendentes = df_filtrado[df_filtrado["STATUS"] == "PENDENTE"]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

# CSS para destacar o botão de download
st.markdown("""
<style>
div.stDownloadButton > button {
    background-color: #ff4b4b;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    padding: 12px 24px;
    animation: blink 1s infinite;
}
@keyframes blink {
  0%   {opacity: 1;}
  50%  {opacity: 0.4;}
  100% {opacity: 1;}
}
</style>
""", unsafe_allow_html=True)

st.download_button(
    label="⬇️ Baixar Pendentes (Excel)",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- 📋 TABELA DE PENDENTES ---
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "DATA_INSPECAO", "STATUS"]])
