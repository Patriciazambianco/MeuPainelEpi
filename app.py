import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ===================================================
# 🌈 TEMA DARK RAINBOW SOFT - COMPLETO
# ===================================================
st.set_page_config(page_title="Painel Check List EPI", layout="wide")

st.markdown("""
<style>

    /* Fundo geral */
    .stApp {
        background-color: #0b0b10 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #101016 !important;
        border-right: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0px 0px 12px rgba(0, 200, 255, 0.15);
    }

    /* Títulos neon */
    h1, h2, h3 {
        background: linear-gradient(90deg, #ff66c4, #9b5bff, #4deeea);
        -webkit-background-clip: text;
        color: transparent !important;
        font-weight: 900 !important;
        text-shadow: 0px 0px 12px rgba(150,50,255,0.35);
    }

    /* Texto geral */
    html, body, div, span, label {
        color: #e5e5e5 !important;
    }

    /* Métricas / Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(255,0,200,0.18), rgba(0,200,255,0.18));
        border-radius: 14px !important;
        padding: 15px !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        box-shadow: 0 0 15px rgba(0,200,255,0.25) !important;
    }

    /* Botões */
    .stButton>button {
        background: linear-gradient(135deg, #7c3aed, #06b6d4) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.65rem 1.2rem !important;
        box-shadow: 0 0 12px rgba(0,200,255,0.4) !important;
        transition: 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: scale(1.04);
        box-shadow: 0 0 18px rgba(0,200,255,0.8) !important;
    }

    /* Tabelas */
    .stDataFrame {
        background-color: #15151c !important;
        border-radius: 10px !important;
        border: 1px solid rgba(0,200,255,0.25) !important;
        box-shadow: 0 0 12px rgba(0,200,255,0.25) !important;
    }

    /* Plotly Charts Container */
    .stPlotlyChart {
        background-color: #15151c !important;
        padding: 12px !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        box-shadow: 0 0 15px rgba(150,50,255,0.25) !important;
    }

</style>
""", unsafe_allow_html=True)

# =======================================================
# TÍTULO
# =======================================================
st.title("🦺 Check List EPI - Técnicos OK x Pendentes")

# =======================================================
# FUNÇÃO DE LEITURA
# =======================================================
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    if "STATUS_CHECK_LIST" in df.columns:
        df["STATUS_CHECK_LIST"] = (
            df["STATUS_CHECK_LIST"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "CHECK LIST OK": "OK",
                "CHECKLIST OK": "OK",
                "OK": "OK",
                "PENDENTE": "PENDENTE"
            })
        )
    else:
        st.warning("⚠️ A coluna 'STATUS_CHECK_LIST' não existe na base.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    return df

# URL
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
df = carregar_dados(url)

# =======================================================
# SIDEBAR
# =======================================================
st.sidebar.header("🎯 Filtros")

gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique())
coordenadores = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique())

gerente_sel = st.sidebar.selectbox("👩‍💼 Gerente", gerentes)
coord_sel = st.sidebar.selectbox("🧑‍🏭 Coordenador", coordenadores)

df_filtrado = df.copy()
if gerente_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_sel]
if coord_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coord_sel]

# =======================================================
# MÉTRICAS
# =======================================================
total = len(df_filtrado)
qtd_ok = (df_filtrado["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df_filtrado["STATUS_CHECK_LIST"] == "PENDENTE").sum()
perc_ok = round((qtd_ok / total) * 100, 1) if total > 0 else 0
perc_pend = round((qtd_pend / total) * 100, 1) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ OK", qtd_ok)
col2.metric("⚠️ Pendentes", qtd_pend)
col3.metric("📊 % OK", f"{perc_ok}%")
col4.metric("📉 % Pendentes", f"{perc_pend}%")

# =======================================================
# GRÁFICO DE PIZZA (neon dark)
# =======================================================
pie_df = pd.DataFrame({
    "Status": ["OK", "PENDENTE"],
    "Qtd": [qtd_ok, qtd_pend]
})

fig_pizza = px.pie(
    pie_df,
    names="Status",
    values="Qtd",
    hole=0.45,
    title="🎯 Distribuição Geral",
    color="Status",
    color_discrete_map={
        "OK": "#4deeea",
        "PENDENTE": "#ff66c4"
    }
)
fig_pizza.update_layout(
    paper_bgcolor="#0b0b10",
    plot_bgcolor="#0b0b10",
    font_color="white",
    height=330
)

col_p1, col_p2, col_sp = st.columns([1.3, 1.3, 0.2])
col_p1.plotly_chart(fig_pizza, use_container_width=True)

# =======================================================
# GRÁFICOS POR GERENTE
# =======================================================
if "GERENTE" in df_filtrado.columns:
    cont_ger = df_filtrado.groupby(["GERENTE", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0)
    cont_ger["TOTAL"] = cont_ger.sum(axis=1)
    cont_ger["% OK"] = (cont_ger["OK"] / cont_ger["TOTAL"] * 100).fillna(0)
    cont_ger["% PENDENTE"] = (cont_ger["PENDENTE"] / cont_ger["TOTAL"] * 100).fillna(0)
    cont_ger = cont_ger.reset_index()

    df_bar_ger = cont_ger.melt(id_vars=["GERENTE"], value_vars=["% OK", "% PENDENTE"],
                               var_name="STATUS", value_name="PERCENTUAL")
    df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ", "")

    fig_ger = px.bar(
        df_bar_ger, x="GERENTE", y="PERCENTUAL", color="STATUS",
        text=df_bar_ger["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map={"OK": "#4deeea", "PENDENTE": "#ff66c4"},
        barmode="group",
        title="📈 % OK x % Pendentes por Gerente"
    )
    fig_ger.update_layout(
        paper_bgcolor="#0b0b10",
        plot_bgcolor="#0b0b10",
        font_color="white",
        height=350
    )
    st.plotly_chart(fig_ger, use_container_width=True)

# =======================================================
# GRÁFICOS POR COORDENADOR
# =======================================================
if "COORDENADOR" in df_filtrado.columns:
    cont_coord = df_filtrado.groupby(["COORDENADOR", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0)
    cont_coord["TOTAL"] = cont_coord.sum(axis=1)
    cont_coord["% OK"] = (cont_coord["OK"] / cont_coord["TOTAL"] * 100).fillna(0)
    cont_coord["% PENDENTE"] = (cont_coord["PENDENTE"] / cont_coord["TOTAL"] * 100).fillna(0)
    cont_coord = cont_coord.reset_index()

    df_bar_coord = cont_coord.melt(
        id_vars=["COORDENADOR"],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ", "")

    fig_coord = px.bar(
        df_bar_coord, x="COORDENADOR", y="PERCENTUAL", color="STATUS",
        text=df_bar_coord["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map={"OK": "#4deeea", "PENDENTE": "#ff66c4"},
        barmode="group",
        title="📊 % OK x % Pendentes por Coordenador"
    )
    fig_coord.update_layout(
        paper_bgcolor="#0b0b10",
        plot_bgcolor="#0b0b10",
        font_color="white",
        height=350
    )
    st.plotly_chart(fig_coord, use_container_width=True)

# =======================================================
# TABELA DE PENDENTES
# =======================================================
df_pendentes = df_filtrado[df_filtrado["STATUS_CHECK_LIST"] == "PENDENTE"]

st.markdown("### 📋 Técnicos Pendentes")
st.dataframe(df_pendentes[["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS_CHECK_LIST"]])

if not df_pendentes.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pendentes.to_excel(writer, index=False, sheet_name="Pendentes")

    st.download_button(
        label="📥 Baixar Pendentes em Excel",
        data=output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.success("🎉 Nenhum pendente encontrado! Tudo OK!")
