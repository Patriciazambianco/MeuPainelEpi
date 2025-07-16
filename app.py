import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Evolução %", layout="wide")
st.title("🦺 Painel de Inspeções EPI - Evolução de Técnicos OK e Pendentes")

# URL do arquivo raw no GitHub (xlsx)
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normaliza colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Padroniza STATUS
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Remove linhas sem técnico ou produto para análise
df_valid = df.dropna(subset=["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"])

# Filtros na sidebar
st.sidebar.header("Filtros")
gerentes = ["Todos"] + sorted(df_valid["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df_valid["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_filtrado = df_valid.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# Última inspeção por técnico + produto
df_ult = (
    df_filtrado.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
              .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
              [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO"]]
)

# Classificação diária por técnico e data (se múltiplos produtos no dia, agregamos status)
status_diario = df_ult.groupby(["TECNICO", "DATA_INSPECAO"])["STATUS"].apply(list).reset_index()

def classifica_dia(status_list):
    if all(s == "OK" for s in status_list):
        return "OK"
    else:
        return "PENDENTE"

status_diario["CLASSIFICACAO"] = status_diario["STATUS"].apply(classifica_dia)

# Agrega por data: conta técnicos OK e Pendentes por dia
evolucao = status_diario.groupby(["DATA_INSPECAO", "CLASSIFICACAO"]).size().unstack(fill_value=0)

# Calcula percentual diário
evolucao["TOTAL"] = evolucao.sum(axis=1)
evolucao["% OK"] = (evolucao.get("OK", 0) / evolucao["TOTAL"]) * 100
evolucao["% PENDENTE"] = (evolucao.get("PENDENTE", 0) / evolucao["TOTAL"]) * 100
evolucao = evolucao.reset_index()

# Mostra os cards com o último percentual disponível
ultimo = evolucao.iloc[-1]
col1, col2 = st.columns(2)
col1.metric("✅ Último % Técnicos 100% OK", f"{ultimo['% OK']:.1f}%")
col2.metric("⚠️ Último % Técnicos Pendentes", f"{ultimo['% PENDENTE']:.1f}%")

# Gráfico da evolução
fig_evolucao = px.line(
    evolucao, x="DATA_INSPECAO", y=["% OK", "% PENDENTE"],
    labels={"DATA_INSPECAO": "Data", "value": "Percentual (%)", "variable": "Status"},
    title="Evolução diária do percentual de Técnicos OK e Pendentes"
)
fig_evolucao.update_traces(mode="lines+markers")
fig_evolucao.update_layout(yaxis=dict(range=[0, 100]))
fig_evolucao.update_traces(marker=dict(size=8))
fig_evolucao.update_layout(legend_title_text="Status")
fig_evolucao.for_each_trace(lambda t: t.update(line=dict(color="green") if t.name=="% OK" else dict(color="red")))

st.plotly_chart(fig_evolucao, use_container_width=True)

# Função para exportar dados filtrados para Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

st.download_button("⬇️ Baixar Excel filtrado", to_excel(df_filtrado), file_name="painel_epi_filtrado.xlsx")

