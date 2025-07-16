import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# --- LEITURA DO EXCEL NO GITHUB ---
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# --- PADRONIZAÇÃO ---
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# --- OBTER ÚLTIMA INSPEÇÃO POR TÉCNICO + PRODUTO ---
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_inspecao = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO", "STATUS"]]
)
df_completo = pd.merge(tecnicos_produtos, df_inspecao, on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")

# --- FILTROS SIDEBAR ---
st.sidebar.header("Filtros")
gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_filtrado = df_completo.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# --- TÉCNICOS PENDENTES ---
df_pendentes = df_filtrado[df_filtrado["STATUS"] == "PENDENTE"]

# --- BOTÃO DE DOWNLOAD PISCANTE NO TOPO ---
st.markdown("""
<div style="display: flex; justify-content: flex-end; margin-top: -40px;">
    <a href="#" download id="botao-download">
        <button style="
            animation: pulse 1s infinite;
            background-color: red;
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.5em 1.5em;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
        ">⬇️ Baixar Pendentes</button>
    </a>
</div>
<style>
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255,0,0, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(255,0,0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255,0,0, 0); }
}
</style>
""", unsafe_allow_html=True)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

st.download_button(
    label="📥 Clique aqui para baixar Técnicos Pendentes",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download_excel_topo"
)

# --- CARDS DE RESUMO ---
contagem = df_filtrado.groupby("STATUS")["TECNICO"].nunique()
total_ok = contagem.get("OK", 0)
total_pendente = contagem.get("PENDENTE", 0)
total = total_ok + total_pendente
perc_ok = (total_ok / total) * 100 if total > 0 else 0
perc_pendente = (total_pendente / total) * 100 if total > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos OK", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes", f"{total_pendente} ({perc_pendente:.1f}%)")

# --- GRÁFICO DE % POR COORDENADOR ---
contagem_coord = df_filtrado.groupby(["COORDENADOR", "STATUS"])["TECNICO"].nunique().unstack(fill_value=0)
for col in ["OK", "PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col] = 0

contagem_coord["TOTAL"] = contagem_coord["OK"] + contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"] / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"] / contagem_coord["TOTAL"]) * 100
contagem_coord = contagem_coord.reset_index()
contagem_coord["COORDENADOR"] = contagem_coord["COORDENADOR"].fillna("Sem Coordenador")

# Long format para gráfico
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
    labels={"COORDENADOR": "Coordenador", "PERCENTUAL": "Percentual (%)", "STATUS": "Status"},
    title="📊 Percentual de Técnicos OK e Pendentes por Coordenador"
)

fig.update_traces(textposition='outside')
fig.update_layout(yaxis=dict(range=[0, 110]), uniformtext_minsize=8)

st.plotly_chart(fig, use_container_width=True)

# --- TABELA DE PENDENTES VISUAL ---
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS"]])
