import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime, timedelta

# Configuração inicial
st.set_page_config(page_title="Painel EPI - Técnicos OK/Pendentes", layout="wide")
st.title("🦺 INSPEÇÕES EPI")

# =============================
# Função para carregar os dados
# =============================
@st.cache_data
def carregar_dados():
    url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url)
    return df

df = carregar_dados()

# =============================
# Normalização de colunas e textos
# =============================
df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

# Verificar se colunas essenciais existem
if "STATUS_CHECK_LIST" not in df.columns or "DATA_INSPECAO" not in df.columns:
    st.error("⚠️ A planilha precisa ter as colunas 'STATUS CHECK LIST' e 'DATA_INSPECAO'.")
    st.stop()

# Forçar STATUS_CHECK_LIST como string
df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.strip().str.upper()

# Converter datas
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# =============================
# Definir STATUS considerando últimos 180 dias
# =============================
hoje = datetime.today()
limite = hoje - timedelta(days=180)

def definir_status(row):
    if pd.isna(row["DATA_INSPECAO"]):
        return "PENDENTE"
    elif row["DATA_INSPECAO"] < limite:
        return "PENDENTE"
    elif row["STATUS_CHECK_LIST"] == "CHECK LIST OK":
        return "OK"
    else:
        return "PENDENTE"

df["STATUS"] = df.apply(definir_status, axis=1)

# =============================
# Cards de indicadores
# =============================
total = len(df)
ok = len(df[df["STATUS"] == "OK"])
pendente = len(df[df["STATUS"] == "PENDENTE"])

perc_ok = (ok / total * 100) if total > 0 else 0
perc_pendente = (pendente / total * 100) if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Registros", total)
col2.metric("✅ OK", f"{ok} ({perc_ok:.1f}%)")
col3.metric("⚠️ Pendentes", f"{pendente} ({perc_pendente:.1f}%)")

# =============================
# Gráfico de Pizza
# =============================
fig_pizza = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pendente],
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "green", "Pendentes": "red"},
    hole=0.4
)
fig_pizza.update_traces(textinfo="percent+label")
st.plotly_chart(fig_pizza, use_container_width=True)

# =============================
# Gráfico de Tendência últimos 180 dias
# =============================
df_trend = df[df["DATA_INSPECAO"].notna() & (df["DATA_INSPECAO"] >= limite)]
df_trend_grouped = df_trend.groupby(["DATA_INSPECAO", "STATUS"]).size().reset_index(name="QTD")

fig_trend = px.line(
    df_trend_grouped,
    x="DATA_INSPECAO",
    y="QTD",
    color="STATUS",
    color_discrete_map={"OK": "green", "PENDENTE": "red"},
    markers=True,
    title="📈 Tendência de Técnicos OK vs Pendentes (Últimos 180 dias)"
)
st.plotly_chart(fig_trend, use_container_width=True)

# =============================
# Exportar Pendentes para Excel
# =============================
df_pendentes = df[df["STATUS"] == "PENDENTE"]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Pendentes")
    return output.getvalue()

if not df_pendentes.empty:
    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=to_excel(df_pendentes),
        file_name="pendentes_epi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================
# Tabela de Pendentes
# =============================
st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "DATA_INSPECAO", "STATUS"]])
