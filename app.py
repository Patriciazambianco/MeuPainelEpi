import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

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

if "STATUS_CHECK_LIST" not in df.columns or "DATA_INSPECAO" not in df.columns:
    st.error("⚠️ A planilha precisa ter as colunas 'STATUS CHECK LIST' e 'DATA_INSPECAO'.")
    st.stop()

df["STATUS_CHECK_LIST"] = df["STATUS_CHECK_LIST"].astype(str).str.strip().str.upper()
df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

# =============================
# Definir STATUS apenas OK ou PENDENTE
# =============================
df["STATUS"] = df["STATUS_CHECK_LIST"].apply(lambda x: "OK" if x == "CHECK LIST OK" else "PENDENTE")

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
# Gráfico de Tendência incluindo todos os técnicos
# =============================
# Gerar série de datas do primeiro ao último registro
min_data = df['DATA_INSPECAO'].min()
max_data = df['DATA_INSPECAO'].max()
if pd.isna(min_data):
    min_data = pd.Timestamp.today()
if pd.isna(max_data):
    max_data = pd.Timestamp.today()
datas = pd.date_range(start=min_data, end=max_data)

# Agrupar por DATA_INSPECAO e STATUS
df_trend = df.groupby(['DATA_INSPECAO', 'STATUS']).size().reset_index(name='QTD')

# Criar todas as combinações de datas x status
all_status = df['STATUS'].unique()
df_full = pd.DataFrame([(d, s) for d in datas for s in all_status], columns=['DATA_INSPECAO', 'STATUS'])

# Merge e preencher zeros
df_trend_complete = pd.merge(df_full, df_trend, on=['DATA_INSPECAO', 'STATUS'], how='left').fillna(0)

fig_trend = px.line(
    df_trend_complete,
    x='DATA_INSPECAO',
    y='QTD',
    color='STATUS',
    color_discrete_map={'OK': 'green', 'PENDENTE': 'red'},
    markers=True,
    title="📈 Tendência de Técnicos OK vs Pendentes"
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
