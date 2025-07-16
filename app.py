import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Evolução por Coordenador", layout="wide")
st.title("🦺 Evolução diária de Técnicos OK e Pendentes por Coordenador")

# URL do Excel no GitHub (raw)
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padronização colunas e dados
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Strip para evitar erros no filtro
df["GERENTE"] = df["GERENTE"].astype(str).str.strip()
df["COORDENADOR"] = df["COORDENADOR"].astype(str).str.strip()

# Filtrar linhas válidas
df_valid = df.dropna(subset=["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"])

# Sidebar filtros
st.sidebar.header("Filtros")
gerentes = ["Todos"] + sorted(df_valid["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df_valid["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

# Aplicar filtros
df_filtrado = df_valid.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# Última inspeção por técnico + produto
df_ult = (
    df_filtrado.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
              .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
              [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR"]]
)

# Classifica o dia por técnico: OK se TODOS produtos OK, senão Pendente
status_diario = df_ult.groupby(["COORDENADOR", "TECNICO", "DATA_INSPECAO"])["STATUS"].apply(list).reset_index()

def classifica_dia(status_list):
    return "OK" if all(s == "OK" for s in status_list) else "PENDENTE"

status_diario["CLASSIFICACAO"] = status_diario["STATUS"].apply(classifica_dia)

# Agora agrupamos por coordenador + data + status, contando técnicos
evolucao = (
    status_diario.groupby(["COORDENADOR", "DATA_INSPECAO", "CLASSIFICACAO"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Total técnicos por coordenador e data
evolucao["TOTAL"] = evolucao.get("OK", 0) + evolucao.get("PENDENTE", 0)

# Percentuais por coordenador e data
evolucao["% OK"] = (evolucao.get("OK", 0) / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao.get("PENDENTE", 0) / evolucao["TOTAL"]) * 100

# Mostrar cards do último dia geral (considerando filtros)
if not evolucao.empty:
    ultimo_dia = evolucao["DATA_INSPECAO"].max()
    ultimos = evolucao[evolucao["DATA_INSPECAO"] == ultimo_dia]
    pct_ok_geral = (ultimos["OK"].sum() / ultimos["TOTAL"].sum()) * 100
    pct_pendente_geral = (ultimos["PENDENTE"].sum() / ultimos["TOTAL"].sum()) * 100
    c1, c2 = st.columns(2)
    c1.metric("✅ Último % Técnicos 100% OK", f"{pct_ok_geral:.1f}%")
    c2.metric("⚠️ Último % Técnicos Pendentes", f"{pct_pendente_geral:.1f}%")
else:
    st.warning("Sem dados para mostrar métricas.")

# Filtro extra para coordenador no gráfico (se quiser só um coordenador)
coordenadores_graf = evolucao["COORDENADOR"].unique().tolist()
coord_graf_sel = st.sidebar.multiselect("Selecionar Coordenador(s) para o gráfico", coordenadores_graf, default=coordenadores_graf)

# Filtra para o gráfico
evolucao_graf = evolucao[evolucao["COORDENADOR"].isin(coord_graf_sel)]

# Plotar gráfico da evolução com percentual por coordenador
fig = px.line(
    evolucao_graf,
    x="DATA_INSPECAO",
    y=["% OK", "% PENDENTE"],
    color="COORDENADOR",
    line_dash="CLASSIFICACAO",
    labels={
        "DATA_INSPECAO": "Data",
        "value": "Percentual (%)",
        "variable": "Status",
        "COORDENADOR": "Coordenador"
    },
    title="Evolução diária % Técnicos OK e Pendentes por Coordenador"
)

fig.update_traces(mode="lines+markers")
fig.update_layout(yaxis=dict(range=[0, 100]), legend_title_text="Legenda")
# Ajusta cores OK verde, PENDENTE vermelho
for trace in fig.data:
    if "% OK" in trace.name:
        trace.line.color = "green"
    elif "% PENDENTE" in trace.name:
        trace.line.color = "red"

# Adiciona os valores percentuais nos pontos
fig.update_traces(texttemplate='%{y:.1f}%', textposition='top center', textfont=dict(size=9))

st.plotly_chart(fig, use_container_width=True)

# Função para exportar dataframe para Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    output.seek(0)
    return output

# Botão para download
st.download_button(
    label="⬇️ Baixar Excel com dados filtrados",
    data=to_excel(df_filtrado),
    file_name="epi_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
