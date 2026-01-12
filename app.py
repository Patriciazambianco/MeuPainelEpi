meu codigo no gifhub import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(page_title="Painel Check List EPI — Power BI Dark", layout="wide")

# ===========================
# CSS — Tudo Branco, Tudo Dark, Sem Cinza
# ===========================
st.markdown("""
<style>

.stApp {
    background-color: #0b0b0f !important;
}

/* Remove padding */
.block-container {
    padding-top: 1.5rem;
}

/* Texto geral branco */
html, body, [class*="css"] {
    color: #ffffff !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f1114 !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}
section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Títulos */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

/* Cards */
div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    padding: 12px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.metric-label {
    color: #ffffff !important;
    font-size: 14px;
}
.metric-value {
    color: #ffffff !important;
    font-size: 36px !important;
    font-weight: 700;
}

/* Botões */
.stButton>button {
    background-color: #13294b !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

/* DataFrame */
.stDataFrame {
    background-color: #0f1114 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
.stDataFrame * {
    color: #ffffff !important;
}

/* Plotly */
.stPlotlyChart {
    background-color: transparent !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# Título
# ---------------------------
st.title("🦺 Check List OK x Pendentes")

# ---------------------------
# Função de leitura
# ---------------------------
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.astype(str).str.upper().str.strip().str.replace(" ", "_")

    if "STATUS_CHECK_LIST" in df.columns:
        df["STATUS_CHECK_LIST"] = (
            df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip().replace({
                "CHECK LIST OK": "OK",
                "CHECKLIST OK": "OK",
                "OK": "OK",
                "PENDENTE": "PENDENTE"
            })
        )
    else:
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    for col in ["TECNICO", "GERENTE", "COORDENADOR", "PRODUTO_SIMILAR"]:
        if col not in df.columns:
            df[col] = None

    return df

# ---------------------------
# Carregar dados
# ---------------------------
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

try:
    df = carregar_dados(url)
except Exception as e:
    st.error("Erro ao carregar dados:")
    st.exception(e)
    st.stop()

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

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<p class="metric-label">✅ OK</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{qtd_ok}</p>', unsafe_allow_html=True)

with col2:
    st.markdown('<p class="metric-label">⚠️ Pendentes</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{qtd_pend}</p>', unsafe_allow_html=True)

with col3:
    st.markdown('<p class="metric-label">📊 % OK</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{perc_ok:.1f}%</p>', unsafe_allow_html=True)

with col4:
    st.markdown('<p class="metric-label">📉 % Pendentes</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{perc_pend:.1f}%</p>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------
# Tema plotly atualizado
# ---------------------------
def aplicar_tema_plotly(fig):
    fig.update_layout(
        paper_bgcolor="#0b0b0f",
        plot_bgcolor="#0b0b0f",
        font_color="#ffffff",
        title_font_color="#ffffff",
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff")
        )
    )
    # Deixa textos das barras/pizza brancos
    for trace in fig.data:
        if 'text' in trace:
            trace.textfont = dict(color="#ffffff")
    return fig

# ---------------------------
# Pizza geral
# ---------------------------
pie_df = pd.DataFrame({"Status": ["OK", "PENDENTE"], "Qtd": [qtd_ok, qtd_pend]})

fig_pizza = px.pie(
    pie_df, names="Status", values="Qtd", hole=0.45,
    color="Status",
    color_discrete_map={"OK": "#2b8cff", "PENDENTE": "#ff7f50"},
    title="Distribuição Geral"
)

fig_pizza = aplicar_tema_plotly(fig_pizza)
st.plotly_chart(fig_pizza, use_container_width=True)

# ---------------------------
# Por gerente
# ---------------------------
if "GERENTE" in df_f.columns:

    cont_g = (
        df_f.groupby(["GERENTE", "STATUS_CHECK_LIST"])["TECNICO"]
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["OK", "PENDENTE"]:
        if col not in cont_g.columns:
            cont_g[col] = 0

    cont_g["TOTAL"] = cont_g["OK"] + cont_g["PENDENTE"]
    cont_g["% OK"] = (cont_g["OK"] / cont_g["TOTAL"] * 100).fillna(0)
    cont_g["% PENDENTE"] = (cont_g["PENDENTE"] / cont_g["TOTAL"] * 100).fillna(0)

    df_bar_ger = cont_g.melt(
        id_vars=["GERENTE"],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar_ger["STATUS"] = df_bar_ger["STATUS"].str.replace("% ", "")

    fig_ger = px.bar(
        df_bar_ger, x="GERENTE", y="PERCENTUAL",
        color="STATUS",
        barmode="group",
        color_discrete_map={"OK": "#2b8cff", "PENDENTE": "#ff7f50"},
        text=df_bar_ger["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        title="% OK x % Pendentes por Gerente"
    )
    fig_ger = aplicar_tema_plotly(fig_ger)
    st.plotly_chart(fig_ger, use_container_width=True)

# ---------------------------
# Por coordenador
# ---------------------------
if "COORDENADOR" in df_f.columns:

    cont_c = (
        df_f.groupby(["COORDENADOR", "STATUS_CHECK_LIST"])["TECNICO"]
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["OK", "PENDENTE"]:
        if col not in cont_c.columns:
            cont_c[col] = 0

    cont_c["TOTAL"] = cont_c["OK"] + cont_c["PENDENTE"]
    cont_c["% OK"] = (cont_c["OK"] / cont_c["TOTAL"] * 100).fillna(0)
    cont_c["% PENDENTE"] = (cont_c["PENDENTE"] / cont_c["TOTAL"] * 100).fillna(0)

    df_bar_coord = cont_c.melt(
        id_vars=["COORDENADOR"],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar_coord["STATUS"] = df_bar_coord["STATUS"].str.replace("% ", "")

    fig_coord = px.bar(
        df_bar_coord, x="COORDENADOR", y="PERCENTUAL",
        color="STATUS",
        barmode="group",
        color_discrete_map={"OK": "#2b8cff", "PENDENTE": "#ff7f50"},
        text=df_bar_coord["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        title="% OK x % Pendentes por Coordenador"
    )
    fig_coord = aplicar_tema_plotly(fig_coord)
    st.plotly_chart(fig_coord, use_container_width=True)

st.markdown("---")

# ---------------------------
# Pendentes + Download
# ---------------------------
df_pend = df_f[df_f["STATUS_CHECK_LIST"] == "PENDENTE"]

st.subheader("Técnicos Pendentes")

cols_mostrar = [
    c for c in ["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS_CHECK_LIST"]
    if c in df_pend.columns
]

st.dataframe(df_pend[cols_mostrar].reset_index(drop=True))

if not df_pend.empty:

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_pend.to_excel(writer, index=False, sheet_name="Pendentes")

    st.download_button(
        "📥 Baixar Pendentes",
        output.getvalue(),
        file_name="Pendentes_EPI.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.success("Nenhum pendente encontrado — tudo OK 🎉")
