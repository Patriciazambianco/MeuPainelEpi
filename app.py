st.markdown("""
<style>
/* Fundo geral e tipografia */
.stApp { background-color: #0b0b0f !important; }
html, body, [class*="css"] { color: #ffffff !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f1114 !important;
    border-right: 1px solid rgba(255,255,255,0.03);
}

/* Títulos */
h1, h2, h3, label, p, span {
    color: #ffffff !important;
}

/* Métricas */
div[data-testid="metric-container"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)) !important;
    border-radius: 10px !important;
    padding: 12px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
}

/* COR DOS TEXTOS DAS MÉTRICAS */
div[data-testid="metric-container"] div, 
div[data-testid="metric-container"] svg, 
div[data-testid="metric-container"] span {
    color: #ffffff !important;
    fill: #ffffff !important;
}

/* Botões */
.stButton>button {
    background-color: #13294b !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}

/* Dataframe */
.stDataFrame {
    background-color: #0f1114 !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.03) !important;
}

/* Plotly container */
.stPlotlyChart {
    background-color: transparent !important;
    padding: 8px !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)
