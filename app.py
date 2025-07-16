import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI - FINAL", layout="wide")

# 1. Carrega do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# 2. Limpa e padroniza colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# 3. Padroniza STATUS
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# 4. Converte DATA
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# 5. Última inspeção por técnico + produto
df_ultimas = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False])
df_ultimas = df_ultimas.drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# 6. Gera base completa (TODOS técnicos x produtos)
tecnicos = df[["TECNICO", "GERENTE", "COORDENADOR"]].drop_duplicates()
produtos = df["PRODUTO_SIMILAR"].dropna().unique()
df_base = tecnicos.assign(key=1).merge(pd.DataFrame({"PRODUTO_SIMILAR": produtos, "key": 1}), on="key").drop("key", axis=1)

# 7. Junta com as últimas inspeções
df_final = pd.merge(df_base, df_ultimas[["TECNICO", "PRODUTO_SIMILAR", "STATUS"]],
                    on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

# 8. Classifica por técnico
def classificar_status(statuses):
    if statuses.isna().all():
        return "SEM INSPECAO"
    if "PENDENTE" in statuses.values:
        return "PENDENTE"
    if "OK" in statuses.values:
        return "OK"
    return "SEM INSPECAO"

df_status = df_final.groupby(["TECNICO", "GERENTE", "COORDENADOR"])["STATUS"] \
    .apply(classificar_status).reset_index(name="STATUS_RESUMO")

# 9. Filtros
coordenadores = sorted(df_status["COORDENADOR"].dropna().unique())
status_opcoes = sorted(df_status["STATUS_RESUMO"].unique())

col1, col2 = st.columns(2)
coord_filtro = col1.selectbox("Filtrar por Coordenador", ["Todos"] + coordenadores)
status_filtro = col2.multiselect("Filtrar por Status", status_opcoes, default=status_opcoes)

df_filtrado = df_status.copy()
if coord_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coord_filtro]
if status_filtro:
    df_filtrado = df_filtrado[df_filtrado["STATUS_RESUMO"].isin(status_filtro)]

# 10. Indicadores
total = len(df_filtrado)
ok = (df_filtrado["STATUS_RESUMO"] == "OK").sum()
pend = (df_filtrado["STATUS_RESUMO"] == "PENDENTE").sum()
sem = (df_filtrado["STATUS_RESUMO"] == "SEM INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

st.markdown("## ✅ Indicadores Gerais")
k1, k2, k3 = st.columns(3)
k1.metric("Técnicos OK", ok, f"{pct_ok}%")
k2.metric("Pendentes", pend, f"{pct_pend}%")
k3.metric("Sem Inspeção", sem, f"{pct_sem}%")

# 11. Gráfico de pizza
contagem = df_filtrado["STATUS_RESUMO"].value_counts().reset_index()
contagem.columns = ["STATUS", "QTD"]
fig_pizza = px.pie(contagem, names="STATUS", values="QTD", title="Distribuição de Status")
st.plotly_chart(fig_pizza, use_container_width=True)

# 12. Ranking por Coordenador
ranking = df_filtrado.groupby("COORDENADOR")["STATUS_RESUMO"].value_counts().unstack(fill_value=0).reset_index()
for status in ["OK", "PENDENTE", "SEM INSPECAO"]:
    if status not in ranking.columns:
        ranking[status] = 0

fig_ranking = px.bar(ranking,
                     x="COORDENADOR",
                     y=["OK", "PENDENTE", "SEM INSPECAO"],
                     title="Ranking por Coordenador",
                     barmode="group")
st.plotly_chart(fig_ranking, use_container_width=True)

# 13. Tabela detalhada
st.markdown("### 📋 Tabela Detalhada")
st.dataframe(df_filtrado)

# 14. Download
def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Status Técnicos")
    buffer.seek(0)
    return buffer

excel_data = gerar_excel(df_filtrado)
st.download_button(
    label="⬇️ Baixar Excel",
    data=excel_data,
    file_name="status_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
