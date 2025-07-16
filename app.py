import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel Técnico - EPI", layout="wide")

# 📥 1. Lê Excel do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# 🧼 2. Padroniza colunas e status
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# 🕒 3. Converte datas
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# 📌 4. Última inspeção por técnico
df_ultimos = df.sort_values(["TECNICO", "DATA_INSPECAO"], ascending=[True, False])
df_ultimos = df_ultimos.drop_duplicates(subset=["TECNICO"], keep="first")

# 📎 5. Junta com todos os técnicos
tecnicos = df[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_completo = pd.merge(tecnicos, df_ultimos[["TECNICO", "STATUS"]], on="TECNICO", how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM INSPECAO")

# 🎛️ 6. Filtros
coord = st.selectbox("📌 Filtrar por Coordenador", ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique()))
status_opcao = st.multiselect(
    "🎯 Filtrar por Status",
    options=["OK", "PENDENTE", "SEM INSPECAO"],
    default=["OK", "PENDENTE", "SEM INSPECAO"]
)

df_filtro = df_completo.copy()
if coord != "Todos":
    df_filtro = df_filtro[df_filtro["COORDENADOR"] == coord]

df_filtro = df_filtro[df_filtro["STATUS"].isin(status_opcao)]

# 📊 7. Indicadores
total = len(df_filtro)
ok = (df_filtro["STATUS"] == "OK").sum()
pend = (df_filtro["STATUS"] == "PENDENTE").sum()
sem = (df_filtro["STATUS"] == "SEM INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

# 🧾 8. Métricas
st.markdown("## 📈 Indicadores Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("✔️ Técnicos OK", ok, f"{pct_ok}%")
col2.metric("⚠️ Pendentes", pend, f"{pct_pend}%")
col3.metric("❌ Sem Inspeção", sem, f"{pct_sem}%")

# 🍕 9. Pizza
pizza = df_filtro["STATUS"].value_counts().reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(pizza, names="STATUS", values="QTD", title="Distribuição de Técnicos")
st.plotly_chart(fig_pie, use_container_width=True)

# 🔄 10. Alternador para gráfico percentual ou absoluto
modo_percentual = st.toggle("🔁 Ver gráfico por percentual (%)", value=True)

if modo_percentual:
    # Percentual por coordenador
    ranking = (
        df_completo
        .groupby("COORDENADOR")["STATUS"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["OK", "PENDENTE", "SEM INSPECAO"]:
        if col not in ranking.columns:
            ranking[col] = 0
    ranking[["OK", "PENDENTE", "SEM INSPECAO"]] *= 100

    fig_rank = px.bar(
        ranking,
        x="COORDENADOR",
        y=["OK", "PENDENTE", "SEM INSPECAO"],
        barmode="stack",
        title="Distribuição (%) por Coordenador",
        labels={"value": "%", "variable": "Status"},
        height=400
    )
    fig_rank.update_layout(yaxis_title="%")
else:
    # Absoluto por coordenador
    ranking = (
        df_completo
        .groupby("COORDENADOR")["STATUS"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["OK", "PENDENTE", "SEM INSPECAO"]:
        if col not in ranking.columns:
            ranking[col] = 0

    fig_rank = px.bar(
        ranking,
        x="COORDENADOR",
        y=["OK", "PENDENTE", "SEM INSPECAO"],
        barmode="group",
        title="Total de Técnicos por Coordenador",
        labels={"value": "Qtd", "variable": "Status"},
        height=400
    )
    fig_rank.update_layout(yaxis_title="Qtd")

st.plotly_chart(fig_rank, use_container_width=True)

# 📋 11. Tabela
st.markdown("### 📋 Técnicos filtrados")
st.dataframe(df_filtro)

# 💾 12. Exportação
def gerar_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Painel Técnicos")
    buffer.seek(0)
    return buffer

st.download_button(
    label="⬇️ Baixar Excel",
    data=gerar_excel(df_filtro),
    file_name="painel_tecnicos_status.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
