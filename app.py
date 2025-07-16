import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel EPI com Gráficos", layout="wide")

# Carrega os dados
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)
df.columns = df.columns.str.upper().str.strip()
df = df.rename(columns={"STATUS CHECK LIST": "STATUS", "DATA INSPECAO": "DATA_INSPECAO"})
df["STATUS CHECK LIST"] = df["STATUS CHECK LIST"].astype(str).str.upper().str.strip()
df["STATUS CHECK LIST"] = df["STATUS CHECK LIST"].replace({"CHECK LIST OK": "OK", "PENDENTE": "PENDENTE"})
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# Pega a última inspeção por TECNICO + PRODUTO
df_ultimas = df.sort_values(["TECNICO", "PRODUTO_SIMILAR", "DATA_INSPECAO"], ascending=[True, True, False]) \
               .drop_duplicates(subset=["TECNICO", "PRODUTO_SIMILAR"], keep="first")

# Base completa para garantir todos TECNICO + PRODUTO
df_base = df[["TECNICO", "PRODUTO_SIMILAR", "GERENTE", "COORDENADOR"]].drop_duplicates()
df_final = pd.merge(df_base, df_ultimas[["TECNICO", "PRODUTO_SIMILAR", "STATUS CHECK LIST"]], 
                    on=["TECNICO", "PRODUTO_SIMILAR"], how="left")

# Classifica status final por técnico
def classificar_status(statuses):
    if statuses.isna().all():
        return "SEM INSPECAO"
    if "PENDENTE" in statuses.values:
        return "PENDENTE"
    if "OK" in statuses.values:
        return "OK"
    return "SEM INSPECAO"

status_tecnicos = df_final.groupby(["TECNICO", "GERENTE", "COORDENADOR"])["STATUS CHECK LIST"] \
    .apply(classificar_status).reset_index(name="STATUS_RESUMO")

# Filtros interativos
coordenadores = sorted(status_tecnicos["COORDENADOR"].dropna().unique())
status_options = sorted(status_tecnicos["STATUS_RESUMO"].unique())

col1, col2 = st.columns(2)
coord_selected = col1.selectbox("Filtrar por COORDENADOR", ["Todos"] + coordenadores)
status_selected = col2.multiselect("Filtrar por STATUS", status_options, default=status_options)

# Aplica os filtros
df_filtered = status_tecnicos.copy()
if coord_selected != "Todos":
    df_filtered = df_filtered[df_filtered["COORDENADOR"] == coord_selected]
if status_selected:
    df_filtered = df_filtered[df_filtered["STATUS_RESUMO"].isin(status_selected)]

# KPIs atualizados
total = len(df_filtered)
ok = (df_filtered["STATUS_RESUMO"] == "OK").sum()
pend = (df_filtered["STATUS_RESUMO"] == "PENDENTE").sum()
sem = (df_filtered["STATUS_RESUMO"] == "SEM INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

st.markdown("## Indicadores Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("Técnicos OK", ok, f"{pct_ok}%")
col2.metric("Pendentes", pend, f"{pct_pend}%")
col3.metric("Sem inspeção", sem, f"{pct_sem}%")

# Gráfico de pizza
status_count = df_filtered["STATUS_RESUMO"].value_counts().reset_index()
status_count.columns = ["STATUS", "QTD"]
fig_pizza = px.pie(status_count, names="STATUS", values="QTD", title="Distribuição de Status")
st.plotly_chart(fig_pizza, use_container_width=True)

# Gráfico por coordenador
ranking = df_filtered.groupby("COORDENADOR")["STATUS_RESUMO"].value_counts().unstack().fillna(0).reset_index()
fig_ranking = px.bar(ranking, x="COORDENADOR", y=["OK", "PENDENTE", "SEM INSPECAO"],
                     title="Ranking por Coordenador", barmode="group")
st.plotly_chart(fig_ranking, use_container_width=True)

# Tabela detalhada
st.markdown("### Tabela Detalhada")
st.dataframe(df_filtered)

# Botão de download
def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Status_Tecnicos')
    output.seek(0)
    return output

excel = gerar_excel_download(df_filtered)
st.download_button(
    label="⬇️ Baixar Excel com Status",
    data=excel,
    file_name="status_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
