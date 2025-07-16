import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Evolução %", layout="wide")

# Estilo para o botão piscante no topo
st.markdown("""
    <style>
    .blinking-button {
        animation: blinker 1s linear infinite;
        color: white !important;
        background-color: #ff4b4b;
        padding: 0.6em 1em;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
    }

    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    </style>
""", unsafe_allow_html=True)

# Leitura dos dados
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Técnicos + Produto únicos
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR", "GERENTE"]]
)

df_completo = pd.merge(tecnicos_produtos, df_ult, on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")
df_completo["DATA_INSPECAO"] = pd.to_datetime(df_completo["DATA_INSPECAO"])

# Filtros
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

# Classifica por técnico + dia
status_diario = df_filtrado.groupby(["TECNICO", "DATA_INSPECAO"])["STATUS"].apply(list).reset_index()

def classifica_dia(status_list):
    return "OK" if all(s == "OK" for s in status_list) else "PENDENTE"

status_diario["CLASSIFICACAO"] = status_diario["STATUS"].apply(classifica_dia)
evolucao = status_diario.groupby(["COORDENADOR", "DATA_INSPECAO", "CLASSIFICACAO"]).size().unstack(fill_value=0).reset_index()
for col in ["OK", "PENDENTE"]:
    if col not in evolucao.columns:
        evolucao[col] = 0

evolucao["TOTAL"] = evolucao["OK"] + evolucao["PENDENTE"]
evolucao["% OK"] = (evolucao["OK"] / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao["PENDENTE"] / evolucao["TOTAL"]) * 100

# Últimos cards
ultimo_geral = evolucao.groupby("DATA_INSPECAO").sum().sort_index().iloc[-1]
st.title("🦺 Painel de Inspeções EPI - Evolução de Técnicos OK e Pendentes")

# Botão piscante no topo
link_download = f"<a href='/app_download' class='blinking-button'>⬇️ Baixar Excel com Pendentes</a>"
st.markdown(link_download, unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("✅ Último % Técnicos 100% OK", f"{(ultimo_geral['OK'] / ultimo_geral['TOTAL'] * 100):.1f}%")
col2.metric("⚠️ Último % Técnicos Pendentes", f"{(ultimo_geral['PENDENTE'] / ultimo_geral['TOTAL'] * 100):.1f}%")

# Dados para gráfico
long = evolucao.melt(id_vars=["COORDENADOR", "DATA_INSPECAO"], value_vars=["% OK", "% PENDENTE"], var_name="STATUS", value_name="PERCENTUAL")
fig = px.line(long, x="DATA_INSPECAO", y="PERCENTUAL", color="COORDENADOR", line_dash="STATUS",
              labels={"PERCENTUAL": "%", "DATA_INSPECAO": "Data"},
              title="Evolução % OK e Pendentes por Coordenador")
fig.update_traces(mode="lines+markers")
for trace in fig.data:
    if "OK" in trace.name:
        trace.line.color = "green"
    elif "PENDENTE" in trace.name:
        trace.line.color = "red"
st.plotly_chart(fig, use_container_width=True)

# Exporta apenas pendentes
pendentes = df_filtrado[df_filtrado["STATUS"] == "PENDENTE"]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

st.download_button(
    label="⬇️ Baixar Excel com Pendentes",
    data=to_excel(pendentes),
    file_name="pendentes_epi.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
