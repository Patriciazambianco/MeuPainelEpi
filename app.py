import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

st.set_page_config(page_title="Painel Inspeções EPI", layout="wide")

# Simulação do carregamento dos dados (substitua pela sua fonte real)
@st.cache_data
def carregar_dados():
    # Exemplo genérico, substitua pela sua planilha/excel
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

df_raw = carregar_dados()

# Garantir que a coluna SALDO SGM TÉCNICO seja string e sem NaN
df_raw["SALDO SGM TÉCNICO"] = df_raw["SALDO SGM TÉCNICO"].fillna("Não tem no saldo").astype(str).str.strip()

# Filtrar apenas pendentes (sem data de inspeção)
df_pendentes = df_raw[df_raw["DATA_INSPECAO"].isna()]

# Escolher colunas que você quer exibir
colunas_exibir = ["TÉCNICO", "FUNCAO", "PRODUTO_SIMILAR", "SUPERVISOR", "SALDO SGM TÉCNICO"]
df_pendentes_display = df_pendentes[colunas_exibir].fillna("").astype(str)

# JavaScript para colorir SALDO SGM TÉCNICO
js_code = JsCode("""
function(params) {
    if (!params.value) return {};
    let val = params.value.toLowerCase();
    if (val.includes('não tem no saldo') || val.includes('nao tem no saldo')) {
        return {
            'color': '#721c24',
            'backgroundColor': '#f8d7da',
            'fontWeight': 'bold'
        };
    }
    if (val.includes('tem no saldo')) {
        return {
            'color': '#856404',
            'backgroundColor': '#fff3cd',
            'fontWeight': 'bold'
        };
    }
    return {};
}
""")

grid_builder = GridOptionsBuilder.from_dataframe(df_pendentes_display)
grid_builder.configure_column("SALDO SGM TÉCNICO", cellStyle=js_code)
gridOptions = grid_builder.build()

AgGrid(
    df_pendentes_display,
    gridOptions=gridOptions,
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    theme="fresh",
    height=400,
)
