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

# Padronizar a coluna STATUS_CHECK_LIST
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()

# Mapear para simplificar status
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# Converter data inspeção para datetime, ignorando erros
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Filtrar linhas com técnico, produto e data inspeção
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

# Obter última inspeção por técnico + produto
df_ult = (
    df_filtrado.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
              .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
              [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO"]]
)

# Classificação diária por técnico (considera se todos produtos do dia estão OK ou se algum pendente)
status_diario = df_ult.groupby(["TECNICO", "DATA_INSPECAO"])["STATUS"].apply(list).reset_index()

def classifica_dia(status_list):
    if all(s == "OK" for s in status_list):
        return "OK"
    else:
        return "PENDENTE"

status_diario["CLASSIFICACAO"] = status_diario["STATUS"].apply(classifica_dia)

# Agrupar por data para contar técnicos OK e Pendentes por dia
evolucao = status_diario.groupby(["DATA_INSPECAO", "CLASSIFICACAO"]).size().unstack(fill_value=0)

# Calcular total e percentuais
evolucao["TOTAL"] = evolucao.sum(axis=1)
evolucao["% OK"] = (evolucao.get("OK", 0) / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao.get("PENDENTE", 0) / evolucao["TOTAL"]) * 100
evolucao = evolucao.reset_index()

# Mostrar cards com os valores mais recentes
ultimo = evolucao.iloc[-1]
col1, col2 = st.columns(2)
col1.metric("✅ Último % Técnicos 100% OK", f"{ultimo['% OK']:.1f}%")
col2.metric("⚠️ Último % Técnicos Pendentes", f"{ultimo['% PENDENTE']:.1f}%")

# Plotar gráfico da evolução
fig_evolucao = px.line(
    evolucao, x="DATA_INSPECAO", y=["% OK", "% PENDENTE"],
    labels={"DATA_INSPECAO": "Data", "value": "Percentual (%)", "variable": "Status"},
    title="Evolução diária do percentual de Técnicos OK e Pendentes"
)
fig_evolucao.update_traces(mode="lines+markers")
fig_evolucao.update_layout(yaxis=dict(range=[0, 100]), legend_title_text="Status")
fig_evolucao.for_each_trace(
    lambda t: t.update(line_color="green") if t.name == "% OK" else t.update(line_color="red")
)

st.plotly_chart(fig_evolucao, use_container_width=True)

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
