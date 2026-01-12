import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(
    page_title="Painel Check List EPI — Dark",
    layout="wide"
)

# ---------------------------
# CSS
# ---------------------------
st.markdown("""
<style>
.stApp { background-color: #0b0b0f; }
.block-container { padding-top: 1.5rem; }
html, body, [class*="css"] { color: #ffffff; }
section[data-testid="stSidebar"] {
    background-color: #0f1114;
    border-right: 1px solid rgba(255,255,255,0.05);
}
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 12px;
    border: 1px solid rgba(255,255,255,0.12);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Título
# ---------------------------
st.title("🦺 Check List OK x Pendentes")

# ---------------------------
# Leitura dos dados
# ---------------------------
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)

    # Padroniza colunas
    df.columns = (
        df.columns.astype(str)
        .str.upper()
        .str.strip()
        .str.replace(" ", "_")
    )

    # Garante colunas base
    for col in ["TECNICO", "GERENTE", "COORDENADOR", "PRODUTO_SIMILAR"]:
        if col not in df.columns:
            df[col] = None

    # DATA_INSPECAO
    if "DATA_INSPECAO" in df.columns:
        df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    else:
        df["DATA_INSPECAO"] = pd.NaT

    # Calcula dias pendentes
    hoje = pd.Timestamp.today().normalize()
    df["DIAS_PENDENTES"] = (hoje - df["DATA_INSPECAO"]).dt.days

    # Status correto
    df["STATUS_CHECK_LIST"] = df["DIAS_PENDENTES"].apply(
        lambda x: "PENDENTE" if pd.notna(x) and x >= 180 else "OK"
    )

    return df

# ---------------------------
# Carregar dados
# ---------------------------
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

df = carregar_dados(url)

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.header("Filtros")

gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique().tolist())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique().tolist())

gerente_sel = st.sidebar.selectbox("Gerente", gerentes)
coord_sel = st.sidebar.selectbox("Coordenador", coordenadores)

df_f = df.copy()
if gerente_sel != "Todos":
    df_f = df_f[df_f["GERENTE"] == gerente_sel]
if coord_sel != "Todos":
    df_f = df_f[df_f["COORDENADOR"] == coord_sel]

# ---------------------------
# Métricas
# ---------------------------
total = len(df_f)
qtd_ok = int((df_f["STATUS_CHECK_LIST"] == "OK").sum())
qtd_pend = int((df_f["STATUS_CHECK_LIST"] == "PENDENTE").sum())

perc_ok = round(qtd_ok / total * 100, 1) if total else 0
perc_pend = round(qtd_pend / total * 100, 1) if total else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ OK", qtd_ok)
c2.metric("⚠️ Pendentes", qtd_pend)
c3.metric("📊 % OK", f"{perc_ok}%")
c4.metric("📉 % Pendentes", f"{perc_pend}%")

st.markdown("---")

# ---------------------------
# Pizza geral
# ---------------------------
pie_df = pd.DataFrame({
    "Status": ["OK", "PENDENTE"],
    "Qtd": [qtd_ok, qtd_pend]
})

fig_pizza = px.pie(
    pie_df,
    names="Status",
    values="Qtd",
    hole=0.45,
    color="Status",
    color_discrete_map={"OK": "#2b8cff", "PENDENTE": "#ff7f50"},
    title="Distribuição Geral"
)

fig_pizza.update_layout(
    paper_bgcolor="#0b0b0f",
    plot_bgcolor="#0b0b0f",
    font_color="#ffffff"
)

st.plotly_chart(fig_pizza, use_container_width=True)

st.markdown("---")

# ---------------------------
# Tabela de pendentes
# ---------------------------
df_pend = df_f[df_f["STATUS_CHECK_LIST"] == "PENDENTE"]

st.subheader("🚨 Técnicos Pendentes (+180 dias)")

cols = [
    "TECNICO",
    "PRODUTO_SIMILAR",
    "DIAS_PENDENTES",
    "COORDENADOR",
    "GERENTE"
]

st.dataframe(df_pend[cols].sort_values("DIAS_PENDENTES", ascending=False))

# ---------------------------
# Download
# ---------------------------
if not df_pend.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pend.to_excel(writer, index=False)

    st.download_button(
        "📥 Baixar Pendentes",
        output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.success("🎉 Nenhum pendente! Tudo em dia.")
