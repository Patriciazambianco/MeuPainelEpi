import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import time

st.set_page_config(page_title="Painel EPI - Evolução %", layout="wide")
st.title("🦺 Painel de Inspeções EPI - Evolução de Técnicos OK e Pendentes")

# URL do Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padronização
colunas_renomeadas = df.columns.str.upper().str.strip().str.replace(" ", "_")
df.columns = colunas_renomeadas

df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Técnicos + Produtos únicos (pra identificar quem não teve inspeção)
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Pegar última inspeção de cada técnico + produto
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO"]]
)

# Merge para incluir quem não fez inspeção
df_completo = pd.merge(tecnicos_produtos, df_ult,
                       on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")

# === SIDEBAR ===
st.sidebar.header("Filtros")
lista_gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
lista_coord = ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique())

filtro_gerente = st.sidebar.selectbox("Gerente", lista_gerentes)
filtro_coord = st.sidebar.selectbox("Coordenador", lista_coord)

# Aplica os filtros
df_filt = df_completo.copy()
if filtro_gerente != "Todos":
    df_filt = df_filt[df_filt["GERENTE"] == filtro_gerente]
if filtro_coord != "Todos":
    df_filt = df_filt[df_filt["COORDENADOR"] == filtro_coord]

# Classificação por técnico + dia
status_dia = df_filt.groupby(["TECNICO", "DATA_INSPECAO"])["STATUS"].apply(list).reset_index()
def classifica(lista):
    if all(s == "OK" for s in lista):
        return "OK"
    return "PENDENTE"
status_dia["CLASSIFICACAO"] = status_dia["STATUS"].apply(classifica)

# Evolução por Coordenador + Data
evolucao = status_dia.merge(df_filt[["TECNICO", "COORDENADOR"]].drop_duplicates(), on="TECNICO")
evolucao = evolucao.groupby(["COORDENADOR", "DATA_INSPECAO", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()

# Garante colunas
for col in ["OK", "PENDENTE"]:
    if col not in evolucao.columns:
        evolucao[col] = 0

evolucao["TOTAL"] = evolucao["OK"] + evolucao["PENDENTE"]
evolucao["% OK"] = (evolucao["OK"] / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao["PENDENTE"] / evolucao["TOTAL"]) * 100

# === METRICAS ===
ultimo_geral = evolucao.groupby("DATA_INSPECAO").sum().sort_index().iloc[-1]
st.markdown("## Indicadores Gerais")
col1, col2 = st.columns(2)
col1.metric("✅ % Técnicos 100% OK", f"{(ultimo_geral['OK'] / ultimo_geral['TOTAL'] * 100):.1f}%")
col2.metric("⚠️ % Técnicos Pendentes", f"{(ultimo_geral['PENDENTE'] / ultimo_geral['TOTAL'] * 100):.1f}%")

# === GRÁFICO DE EVOLUÇÃO ===
evolucao_long = evolucao.melt(
    id_vars=["COORDENADOR", "DATA_INSPECAO"],
    value_vars=["% OK", "% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)

fig = px.line(
    evolucao_long,
    x="DATA_INSPECAO",
    y="PERCENTUAL",
    color="COORDENADOR",
    line_dash="STATUS",
    labels={"DATA_INSPECAO": "Data", "PERCENTUAL": "%", "COORDENADOR": "Coordenador"},
    title="Evolução % de Técnicos OK e Pendentes por Coordenador"
)
fig.update_traces(mode="lines+markers")
fig.update_layout(yaxis=dict(range=[0, 100]))

# Colorir linhas
for trace in fig.data:
    if "OK" in trace.name:
        trace.line.color = "green"
    elif "PENDENTE" in trace.name:
        trace.line.color = "red"

st.plotly_chart(fig, use_container_width=True)

# === TABELA DE PENDENTES ===
df_pendentes = df_filt[df_filt["STATUS"] == "PENDENTE"]
st.markdown("## 📋 Técnicos Pendentes")
st.dataframe(df_pendentes, use_container_width=True)

# Função exportar Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

# Botão de download com estilo piscante
css = """
<style>
@keyframes piscar {
  0%   {background-color: #ff0000; color: white;}
  50%  {background-color: white; color: red; border: 1px solid red;}
  100% {background-color: #ff0000; color: white;}
}
.blink {
  animation: piscar 1s infinite;
  padding: 0.5em 1em;
  font-weight: bold;
  border-radius: 5px;
  display: inline-block;
  text-align: center;
  margin-bottom: 1em;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

col_top = st.columns(1)[0]
with col_top:
    st.markdown('<div class="blink">⬇️ Baixar Excel com Pendentes</div>', unsafe_allow_html=True)
    st.download_button(
        label="",
        data=to_excel(df_pendentes),
        file_name="tecnicos_pendentes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
