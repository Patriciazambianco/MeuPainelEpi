import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Evolução %", layout="wide")
st.title("🦺 Painel de Inspeções EPI - Evolução Técnicos OK e Pendentes")

# Link direto do Excel no GitHub (raw)
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Normaliza colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Normaliza status e cria coluna simplificada
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# Data inspeção datetime
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Pegando todos técnicos x produtos (pra incluir quem não tem inspeção, fica pendente)
tec_prod = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Última inspeção por técnico + produto (ignora nulos)
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR", "GERENTE"]]
)

# Junta tudo pra garantir técnico x produto sem inspeção aparecem como pendente
df_completo = pd.merge(tec_prod, df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO"]],
                       on=["TECNICO", "PRODUTO_SIMILAR"], how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")

# Sidebar filtros
st.sidebar.header("Filtros")
gerentes = ["Todos"] + sorted(df_completo["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique())
gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coordenador_sel = st.sidebar.selectbox("Coordenador", coordenadores)

# Aplica filtros
df_filtrado = df_completo.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coordenador_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_sel]

# Para calcular % OK e Pendentes, vamos considerar cada técnico como "OK" se TODOS os seus produtos estão OK
# Agrupa por técnico, verifica status dos produtos
status_por_tecnico = (
    df_filtrado.groupby(["TECNICO", "COORDENADOR"])["STATUS"]
    .apply(lambda x: "OK" if all(s == "OK" for s in x) else "PENDENTE")
    .reset_index()
)

# Contagem por coordenador e status
contagem_coord = status_por_tecnico.groupby(["COORDENADOR", "STATUS"]).size().unstack(fill_value=0)
contagem_coord["TOTAL"] = contagem_coord.sum(axis=1)

# Percentuais
contagem_coord["% OK"] = (contagem_coord.get("OK", 0) / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord.get("PENDENTE", 0) / contagem_coord["TOTAL"]) * 100

# Cards com percentuais gerais (todos coordenadores juntos)
total_geral = status_por_tecnico["STATUS"].value_counts()
total_tecnicos = total_geral.sum()
pct_ok = total_geral.get("OK", 0) / total_tecnicos * 100 if total_tecnicos > 0 else 0
pct_pend = total_geral.get("PENDENTE", 0) / total_tecnicos * 100 if total_tecnicos > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ % Técnicos OK (todos)", f"{pct_ok:.1f}%")
col2.metric("⚠️ % Técnicos Pendentes (todos)", f"{pct_pend:.1f}%")

# Gráfico ranking coordenadores
fig = px.bar(
    contagem_coord.reset_index(),
    x="COORDENADOR",
    y=["OK", "PENDENTE"],
    title="Quantidade Técnicos OK e Pendentes por Coordenador",
    labels={"value": "Quantidade de Técnicos", "COORDENADOR": "Coordenador", "variable": "Status"},
    color_discrete_map={"OK": "green", "PENDENTE": "red"},
    barmode="group"
)

# Gráfico de % por coordenador
fig_pct = px.bar(
    contagem_coord.reset_index(),
    x="COORDENADOR",
    y=["% OK", "% PENDENTE"],
    title="Percentual de Técnicos OK e Pendentes por Coordenador",
    labels={"value": "Percentual (%)", "COORDENADOR": "Coordenador", "variable": "Status"},
    color_discrete_map={"% OK": "green", "% PENDENTE": "red"},
    barmode="group",
    range_y=[0, 100]
)

st.plotly_chart(fig, use_container_width=True)
st.plotly_chart(fig_pct, use_container_width=True)

# Função exportar Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    output.seek(0)
    return output

st.download_button(
    label="⬇️ Baixar Excel com dados filtrados",
    data=to_excel(df_filtrado),
    file_name="epi_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
