import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Painel Inspeções EPI", layout="wide")

st.title("🦺 Painel de Inspeções EPI - Técnico com Saldo SGM")

# Simulando dados - substitua pela sua carga real
data = {
    "TÉCNICO": ["João", "Maria", "Pedro", "Ana"],
    "FUNCAO": ["Téc 1", "Téc 2", "Téc 3", "Téc 4"],
    "SALDO SGM TÉCNICO": ["Tem no saldo", "Não tem no saldo", "Tem no saldo", "Não tem no saldo"],
    "SUPERVISOR": ["Supervisor 1", "Supervisor 2", "Supervisor 1", "Supervisor 3"]
}
df = pd.DataFrame(data)

# JS para colorir células da coluna SALDO SGM TÉCNICO
cell_style_jscode = JsCode("""
function(params) {
    if (!params.value) return {};
    if (params.value.toLowerCase().includes("não tem no saldo")) {
        return {
            'color': '#721c24',
            'backgroundColor': '#f8d7da',
            'fontWeight': 'bold'
        };
    } else if (params.value.toLowerCase().includes("tem no saldo")) {
        return {
            'color': '#856404',
            'backgroundColor': '#fff3cd',
            'fontWeight': 'bold'
        };
    }
    return {};
}
""")

# Configurando o grid com as colunas e estilo na coluna saldo
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("SALDO SGM TÉCNICO", cellStyle=cell_style_jscode)
gridOptions = gb.build()

AgGrid(df, gridOptions=gridOptions, fit_columns_on_grid_load=True, height=300)
