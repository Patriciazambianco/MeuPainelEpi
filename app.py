import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Evolução %", layout="wide")
st.title("🦺 Painel de Inspeções EPI - Evolução de Técnicos OK e Pendentes")

# URL raw do arquivo Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padronizar nomes das colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Padronizar e mapear STATUS_CHECK_LIST
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# Converter data para datetime, ignorando erros
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Preencher técnicos e produtos únicos para considerar pendentes (sem inspeção)
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Última inspeção por técnico + produto
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR", "GERENTE"]]
)

# Juntar tudo pra incluir técnicos sem inspeção com status 'PENDENTE'
df_completo = pd.merge(tecnicos_produtos, df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO"]],
                       on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")
df_completo["DATA_INSPECAO"] = pd.to_datetime(df_completo["DATA_INSPECAO"])

# Filtros no sidebar
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

# Classificar por técnico + dia + coordenador (pra manter o coordenador no agrupamento)
status_diario = (
    df_filtrado.groupby(["COORDENADOR", "TECNICO", "DATA_INSPECAO"])["STATUS"]
    .apply(list)
    .reset_index()
)

def classifica_dia(status_list):
    if all(s == "OK" for s in status_list):
        return "OK"
    else:
        return "PENDENTE"

status_diario["CLASSIFICACAO"] = status_diario["STATUS"].apply(classifica_dia)

# Evolução: contar técnicos OK e Pendentes por coordenador e data
evolucao = (
    status_diario.groupby(["COORDENADOR", "DATA_INSPECAO", "CLASSIFICACAO"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Garantir colunas para OK e PENDENTE
for col in ["OK", "PENDENTE"]:
    if col not in evolucao.columns:
        evolucao[col] = 0

# Total técnicos por coordenador e data
evolucao["TOTAL"] = evolucao["OK"] + evolucao["PENDENTE"]

# Calcular percentuais
evolucao["% OK"] = (evolucao["OK"] / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao["PENDENTE"] / evolucao["TOTAL"]) * 100

# Mostrar cards com último percentual geral (filtrando antes)
ultimo_geral = evolucao.groupby("DATA_INSPECAO").sum().sort_index().iloc[-1]
col1, col2 = st.columns(2)
col1.metric("✅ Último % Técnicos 100% OK", f"{(ultimo_geral['OK'] / ultimo_geral['TOTAL'] * 100):.1f}%")
col2.metric("⚠️ Último % Técnicos Pendentes", f"{(ultimo_geral['PENDENTE'] / ultimo_geral['TOTAL'] * 100):.1f}%")

# Preparar dados para gráfico (formato longo)
evolucao_long = evolucao.melt(
    id_vars=["COORDENADOR", "DATA_INSPECAO"],
    value_vars=["% OK", "% PENDENTE"],
    var_name="STATUS",
    value_name="PERCENTUAL"
)

# Gráfico de linha com cores e % nos pontos
fig = px.line(
    evolucao_long,
    x="DATA_INSPECAO",
    y="PERCENTUAL",
    color="COORDENADOR",
    line_dash="STATUS",
    labels={
        "DATA_INSPECAO": "Data",
        "PERCENTUAL": "Percentual (%)",
        "STATUS": "Status",
        "COORDENADOR": "Coordenador"
    },
    title="Evolução diária % Técnicos OK e Pendentes por Coordenador"
)
fig.update_traces(mode="lines+markers")
fig.update_layout(yaxis=dict(range=[0, 100]), legend_title_text="Legenda")

# Colorir linhas OK de verde e Pendente de vermelho
for trace in fig.data:
    if "OK" in trace.name:
        trace.line.color = "green"
    elif "PENDENTE" in trace.name:
        trace.line.color = "red"

# Mostrar valores % nos pontos
fig.update_traces(texttemplate='%{y:.1f}%', textposition='top center', textfont=dict(size=9))

st.plotly_chart(fig, use_container_width=True)

# Função para exportar df filtrado para Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    output.seek(0)
    return output

# Botão download
st.download_button(
    label="⬇️ Baixar Excel com dados filtrados",
    data=to_excel(df_filtrado),
    file_name="epi_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
