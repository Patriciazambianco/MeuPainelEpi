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
# Ajuste dos dados
# =============================

# Se não existir coluna "STATUS CHECK LIST", cria uma fictícia só pra rodar
if "STATUS CHECK LIST" not in df.columns:
    st.error("⚠️ Sua planilha precisa ter a coluna 'STATUS CHECK LIST' com os valores 'OK' e 'Pendente'")
    st.stop()

# Normalizar texto
df["STATUS CHECK LIST"] = df["STATUS CHECK LIST"].str.strip().str.upper()

# =============================
# Cálculo de métricas
# =============================
total = len(df)
ok = len(df[df["STATUS CHECK LIST"] == "OK"])
pendente = len(df[df["STATUS CHECK LIST"] != "OK"])

perc_ok = (ok / total * 100) if total > 0 else 0
perc_pendente = (pendente / total * 100) if total > 0 else 0

# =============================
# Cards de indicadores
# =============================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Registros", total)

with col2:
    st.metric("✅ OK", f"{ok} ({perc_ok:.1f}%)")

with col3:
    st.metric("⚠️ Pendentes", f"{pendente} ({perc_pendente:.1f}%)")

# =============================
# Gráfico de Pizza
# =============================
fig = px.pie(
    names=["OK", "Pendentes"],
    values=[ok, pendente],
    color=["OK", "Pendentes"],
    color_discrete_map={"OK": "green", "Pendentes": "red"},
    hole=0.4
)
fig.update_traces(textinfo="percent+label")
st.plotly_chart(fig, use_container_width=True)

# =============================
# Exportar Pendentes para Excel
# =============================
df_pendentes = df[df["STATUS CHECK LIST"] != "OK"]

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
