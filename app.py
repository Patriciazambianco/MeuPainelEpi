<style>
/* Fundo geral */
.stApp { background-color: #0b0b0f !important; }

/* Remove padding lateral padrão */
.block-container { padding-top: 1.5rem; }

/* Texto geral — agora 100% branco */
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

/* Cards / métricas */
div[data-testid="metric-container"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)) !important;
    border-radius: 10px !important;
    padding: 12px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}

/* Label dos cards — branco */
.metric-label {
    color: #ffffff !important;
    font-size: 14px !important;
    margin: 0;
}

/* Valor dos cards — branco */
.metric-value {
    color: #ffffff !important;
    font-size: 36px !important;
    font-weight: 700 !important;
    margin: 0;
}

/* Botões */
.stButton>button {
    background-color: #13294b !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    padding: 6px 12px !important;
}

/* Dataframe (tabela) */
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
    padding: 8px !important;
    border-radius: 10px !important;
}
</style>
