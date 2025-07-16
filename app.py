import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel Técnico - EPI", layout="wide")

# 📥 1. Lê o Excel direto do GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = pd.read_excel(url)

# 🧼 2. Padroniza colunas
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip()

# 🔁 3. Traduz status
df["STATUS"] = df["STATUS_CHECK_LIST"].replace({
    "CHECK LIST OK": "OK",
    "PENDENTE": "PENDENTE"
})

# 🕒 4. Converte datas
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# 🧠 5. Pega última inspeção por técnico (sem produto)
df_ultimos = df.sort_values(["TECNICO", "DATA_INSPECAO"], ascending=[True, False])
df_ultimos = df_ultimos.drop_duplicates(subset=["TECNICO"], keep="first")

# 🧱 6. Junta com todos os técnicos (mesmo sem inspeção)
tecnicos = df[["TECNICO", "COORDENADOR", "GERENTE"]].drop_duplicates()
df_completo = pd.merge(tecnicos, df_ultimos[["TECNICO", "STATUS"]], on="TECNICO", how="left")
df_completo["STATUS"] = df_completo["STATUS"].fillna("SEM INSPECAO")

# 🎛️ 7. Filtro por coordenador
coord = st.selectbox("Filtrar por Coordenador", ["Todos"] + sorted(df_completo["COORDENADOR"].dropna().unique()))
df_filtro = df_completo.copy()
if coord != "Todos":
    df_filtro = df_filtro[df_filtro["COORDENADOR"] == coord]

# 📊 8. Indicadores
total = len(df_filtro)
ok = (df_filtro["STATUS"] == "OK").sum()
pend = (df_filtro["STATUS"] == "PENDENTE").sum()
sem = (df_filtro["STATUS"] == "SEM INSPECAO").sum()

pct_ok = round(ok / total * 100, 1) if total else 0
pct_pend = round(pend / total * 100, 1) if total else 0
pct_sem = round(sem / total * 100, 1) if total else 0

# 🔥 9. KPIs
st.markdown("## 🎯 Indicadores Gerais")
c1, c2, c3 = st.columns(3)
c1.metric("Técnicos OK", ok, f"{pct_ok}%")
c2.metric("Pendentes", pend, f"{pct_pend}%")
c3.metric("Sem Inspeção", sem, f"{pct_sem}%")

# 🍕 10. Gráfico de Pizza
pizza = df_filtro["STATUS"].value_counts().reset_index()
pizza.columns = ["STATUS", "QTD"]
fig_pie = px.pie(pizza, names="STATUS", values="QTD", title="Distribuição de Técnicos")
st.plotly_chart(fig_pie, use_container_width=True)

# 🏆 11. Ranking por Coordenador (corrigido)
ranking = df_completo.groupby("COORDENADOR")["STATUS"].value_counts().unstack().reset_index()

# ✅ Garante que todas as colunas existam
for col in ["OK", "PENDENTE", "SEM INSPECAO"]:
    if col not in ranking.columns:
        ranking[col] = 0

fig_rank = px.bar(
    ranking,
    x="COORDENADOR",
    y=["OK", "PENDENTE", "SEM INSPECAO"],
    barmode="group",
    title="Ranking de Técnicos por Coordenador"
)
st.plotly_chart(fig_rank, use_container_width=True)

# 📋 12. Tabela Detalhada
st.markdown("### 📋 Tabela com Técnicos e Status")
st.dataframe(df_filtro)

# 💾 13. Download da Tabela
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
