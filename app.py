import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 Painel de Técnicos OK e Pendentes por Coordenador")

# URL raw do Excel no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# Padronizar colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Padronizar e mapear STATUS_CHECK_LIST
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# Converter data para datetime (ignorar erros)
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Preencher técnicos e produtos únicos para garantir inclusão de quem não tem inspeção
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE"]].drop_duplicates()

# Última inspeção por técnico + produto
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR", "GERENTE"]]
)

# Merge pra incluir técnicos sem inspeção com status PENDENTE
df_completo = pd.merge(tecnicos_produtos, df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
                       on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")

# Filtros sidebar: Gerente e Coordenador
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

# Contar técnicos OK e Pendentes por coordenador
contagem_coord = df_filtrado.groupby(["COORDENADOR", "STATUS"])["TECNICO"].nunique().unstack(fill_value=0)

# Garantir colunas OK e PENDENTE existam
for col in ["OK", "PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col] = 0

contagem_coord = contagem_coord.reset_index()
contagem_coord["COORDENADOR"] = contagem_coord["COORDENADOR"].fillna("Sem Coordenador")

# Cálculo total e percentual
contagem_coord["TOTAL"] = contagem_coord["OK"] + contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"] / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"] / contagem_coord["TOTAL"]) * 100

# Cards resumo geral
total_ok = contagem_coord["OK"].sum()
total_pendente = contagem_coord["PENDENTE"].sum()
total_geral = total_ok + total_pendente
perc_ok = (total_ok / total_geral) * 100 if total_geral > 0 else 0
perc_pendente = (total_pendente / total_geral) * 100 if total_geral > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos OK (total)", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes (total)", f"{total_pendente} ({perc_pendente:.1f}%)")

# Gráfico barras OK vs Pendentes por coordenador
fig = px.bar(
    contagem_coord,
    x="COORDENADOR",
    y=["OK", "PENDENTE"],
    title="Quantidade de Técnicos OK e Pendentes por Coordenador",
    labels={"value": "Quantidade de Técnicos", "COORDENADOR": "Coordenador", "variable": "Status"},
    color_discrete_map={"OK": "green", "PENDENTE": "red"},
    barmode="group"
)
st.plotly_chart(fig, use_container_width=True)

# Tabela só dos técnicos pendentes (filtrada)
df_pendentes = df_filtrado[df_filtrado["STATUS"] == "PENDENTE"]

st.markdown("### Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS"]])

# Função pra exportar df para Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    output.seek(0)
    return output

# Botão download da tabela pendentes
st.download_button(
    label="⬇️ Baixar Excel com Técnicos Pendentes",
    data=to_excel(df_pendentes),
    file_name="epi_tecnicos_pendentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
