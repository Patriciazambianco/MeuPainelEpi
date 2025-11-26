import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -------------------------------------------------
# 🔥 CSS DARK TOTAL + TEXTO BRANCO DEFINITIVO
# -------------------------------------------------
st.markdown("""
<style>

/* Fundo geral */
.stApp { background-color: #0b0b0f !important; }

/* Container */
.block-container { padding-top: 1.5rem !important; }

/* Todo tipo de texto */
html, body, p, span, div, label, li, td, th, strong, em {
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
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
div[data-testid="metric-container"] * {
    color: #ffffff !important;
}

/* Botões */
.stButton>button {
    background-color: #13294b !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}

/* Tabelas */
.stDataFrame, .stDataFrame * {
    background-color: #0f1114 !important;
    color: #ffffff !important;
}

/* Plotly wrapper */
.stPlotlyChart {
    background-color: transparent !important;
    padding: 8px !important;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 📌 Simulação dos seus dados (substituir pelo real)
# -------------------------------------------------
qtd_ok = 120
qtd_pendente = 40

df = pd.DataFrame({
    "Gestor": ["Ana", "Ana", "Carlos", "Bruno", "Bruno"],
    "Status": ["OK", "PENDENTE", "OK", "OK", "PENDENTE"]
})

# -------------------------------------------------
# 🔍 MÉTRICAS SUPERIORES
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("OK", qtd_ok)
col2.metric("PENDENTES", qtd_pendente)

percent_ok = qtd_ok / (qtd_ok + qtd_pendente)
percent_pen = qtd_pendente / (qtd_ok + qtd_pendente)

col3.metric("% OK", f"{percent_ok*100:.1f}%")
col4.metric("% PENDENTE", f"{percent_pen*100:.1f}%")

st.markdown("---")

# -------------------------------------------------
# 🔥 GRÁFICO DE PIZZA — AGORA COM TEXTO BRANCO
# -------------------------------------------------
fig_pizza = go.Figure(
    data=[
        go.Pie(
            labels=["OK", "PENDENTE"],
            values=[qtd_ok, qtd_pendente],
            hole=0.45,
            textinfo="label+percent",
            pull=[0, 0.05],

            # 👇 AQUI ESTÁ A MÁGICA PRA FICAR BRANCO
            textfont=dict(color="white"),
            insidetextfont=dict(color="white"),
            outsidetextfont=dict(color="white"),
        )
    ]
)

fig_pizza.update_layout(
    showlegend=True,
    legend=dict(font=dict(color="white")),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=260,
)

st.subheader("Status Geral")
st.plotly_chart(fig_pizza, use_container_width=True)

# -------------------------------------------------
# 🔥 GRÁFICO POR GESTOR — TODOS APARECEM
# -------------------------------------------------
gestores = df["Gestor"].unique()

status_por_gestor = df.groupby(["Gestor", "Status"]).size().unstack(fill_value=0)

fig_gestor = go.Figure()

for gestor in gestores:
    ok_val = status_por_gestor.loc[gestor]["OK"] if "OK" in status_por_gestor.columns else 0
    pend_val = status_por_gestor.loc[gestor]["PENDENTE"] if "PENDENTE" in status_por_gestor.columns else 0
    
    fig_gestor.add_trace(
        go.Bar(
            name=gestor,
            x=["OK", "PENDENTE"],
            y=[ok_val, pend_val],
            text=[ok_val, pend_val],
            textposition="outside",
            marker_line_width=0,
            textfont=dict(color="white")
        )
    )

fig_gestor.update_layout(
    barmode="group",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(font=dict(color="white")),
    height=350,
    xaxis=dict(color="white"),
    yaxis=dict(color="white")
)

st.subheader("Status por Gestor")
st.plotly_chart(fig_gestor, use_container_width=True)

# -------------------------------------------------
# 🔥 EXIBIR TABELA
# -------------------------------------------------
st.subheader("Base de Dados")
st.dataframe(df)
