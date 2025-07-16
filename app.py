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

# Preencher técnicos e produtos únicos (para incluir técnicos sem inspeção)
tecnicos_produtos = df[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR"]].drop_duplicates()

# Última inspeção por técnico + produto
df_ult = (
    df.dropna(subset=["DATA_INSPECAO"])
      .sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
      .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")
      [["TECNICO", "PRODUTO_SIMILAR", "STATUS", "DATA_INSPECAO", "COORDENADOR"]]
)

# Merge pra garantir técnicos sem inspeção apareçam como PENDENTE
df_completo = pd.merge(tecnicos_produtos, df_ult[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
                       on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

df_completo["STATUS"] = df_completo["STATUS"].fillna("PENDENTE")

# Contar técnicos OK e Pendentes por coordenador
contagem_coord = df_completo.groupby(["COORDENADOR", "STATUS"])["TECNICO"].nunique().unstack(fill_value=0)

# Garantir colunas OK e PENDENTE existam
for col in ["OK", "PENDENTE"]:
    if col not in contagem_coord.columns:
        contagem_coord[col] = 0

# Fill coordenador nulo com texto para não quebrar o gráfico
contagem_coord = contagem_coord.reset_index()
contagem_coord["COORDENADOR"] = contagem_coord["COORDENADOR"].fillna("Sem Coordenador")

# DEBUG: Mostrar colunas e primeiras linhas para conferir
st.write("Colunas após agrupamento e reset_index:", contagem_coord.columns.tolist())
st.write(contagem_coord.head())

# Gráfico de barras com OK e PENDENTE por coordenador
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

# Cálculo dos percentuais por coordenador
contagem_coord["TOTAL"] = contagem_coord["OK"] + contagem_coord["PENDENTE"]
contagem_coord["% OK"] = (contagem_coord["OK"] / contagem_coord["TOTAL"]) * 100
contagem_coord["% PENDENTE"] = (contagem_coord["PENDENTE"] / contagem_coord["TOTAL"]) * 100

# Mostrar tabela resumida com percentuais
st.write("Percentuais por Coordenador:")
st.dataframe(contagem_coord[["COORDENADOR", "OK", "PENDENTE", "% OK", "% PENDENTE"]])

# Cards com total geral
total_ok = contagem_coord["OK"].sum()
total_pendente = contagem_coord["PENDENTE"].sum()
total_geral = total_ok + total_pendente
perc_ok = (total_ok / total_geral) * 100 if total_geral > 0 else 0
perc_pendente = (total_pendente / total_geral) * 100 if total_geral > 0 else 0

col1, col2 = st.columns(2)
col1.metric("✅ Técnicos OK (total)", f"{total_ok} ({perc_ok:.1f}%)")
col2.metric("⚠️ Técnicos Pendentes (total)", f"{total_pendente} ({perc_pendente:.1f}%)")

# Função pra exportar pra Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output

# Botão para download
st.download_button(
    label="⬇️ Baixar Excel com dados completos",
    data=to_excel(df_completo),
    file_name="epi_tecnicos_status.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
