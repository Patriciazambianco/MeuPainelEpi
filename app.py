import streamlit as st
import plotly.express as px

# ===========================
# ESTILO DARK – CSS COMPLETO
# ===========================
st.markdown("""
<style>

body {
    background-color: #111111;
}

/* Remove padding lateral padrão */
.block-container {
    padding-top: 1.5rem;
}

/* Títulos dos cards */
.metric-label {
    color: #B0B0B0 !important;
    font-size: 14px !important;
}

/* VALORES dos cards – agora BRANCO */
.metric-value {
    color: #FFFFFF !important;
    font-size: 36px !important;
    font-weight: 600 !important;
}

/* Força fundo da página */
.main {
    background-color: #111111;
}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# EXEMPLO DE VARIÁVEIS (substituir pelas suas reais)
# ==========================================================
ok_total = 1462
pend_total = 847
pct_ok = 63.3
pct_pend = 36.7

# ==========================================================
# CARDS
# ==========================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<p class="metric-label">✔️ OK</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{ok_total}</p>', unsafe_allow_html=True)

with col2:
    st.markdown('<p class="metric-label">⚠️ Pendentes</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{pend_total}</p>', unsafe_allow_html=True)

with col3:
    st.markdown('<p class="metric-label">📊 % OK</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{pct_ok:.1f}%</p>', unsafe_allow_html=True)

with col4:
    st.markdown('<p class="metric-label">📉 % Pendentes</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{pct_pend:.1f}%</p>', unsafe_allow_html=True)


# ==========================================================
# GRÁFICO PLOTLY BARRAS – DARK
# ==========================================================
fig1 = px.bar(
    x=["OK", "Pendentes"],
    y=[ok_total, pend_total],
    color=["OK", "Pendentes"],
    title="Status Geral"
)

fig1.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111111",
    plot_bgcolor="#111111",
    font_color="white"
)

st.plotly_chart(fig1, use_container_width=True)


# ==========================================================
# GRÁFICO DE PIZZA – DARK
# ==========================================================
fig2 = px.pie(
    values=[ok_total, pend_total],
    names=["OK", "Pendentes"],
    title="Distribuição Geral"
)

fig2.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111111",
    plot_bgcolor="#111111",
    font_color="white"
)

st.plotly_chart(fig2, use_container_width=True)
