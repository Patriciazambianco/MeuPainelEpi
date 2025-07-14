import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import plotly.express as px

st.set_page_config(page_title="Painel Inspeções EPI", layout="wide")

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    # Ajusta texto em SALDO SGM TÉCNICO e trata valores vazios
    df["SALDO SGM TÉCNICO"] = df["SALDO SGM TÉCNICO"].astype(str).str.strip()
    df.loc[df["SALDO SGM TÉCNICO"].isin(["", "nan", "NaN"]), "SALDO SGM TÉCNICO"] = "Não tem no saldo"
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas_por_tecnico = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates(subset=["TÉCNICO"])
    return pd.concat([ultimas_por_tecnico, sem_data], ignore_index=True)

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

# --- FILTROS ---
gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)
df_filtrado_ger = df_tratado[df_tratado["GERENTE"] == gerente_sel] if gerente_sel != "-- Todos --" else df_tratado.copy()

coordenadores = sorted(df_filtrado_ger["COORDENADOR"].dropna().unique())
coordenador_sel = st.multiselect("Filtrar por Coordenador", coordenadores)
df_filtrado = df_filtrado_ger[df_filtrado_ger["COORDENADOR"].isin(coordenador_sel)] if coordenador_sel else df_filtrado_ger.copy()

# --- FILTRA OS PENDENTES (SEM DATA DE INSPEÇÃO) ---
df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]

# --- KPIs ---
total = len(df_filtrado)
pendentes = len(df_pendentes)
ok = total - pendentes
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pendentes = round(100 - pct_ok, 1)

st.title("🦺 Painel de Inspeções EPI")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Inspeções OK", ok)
col2.metric("Pendentes", pendentes)
col3.metric("% OK", f"{pct_ok}%")
col4.metric("% Pendentes", f"{pct_pendentes}%")

# --- GRÁFICO POR COORDENADOR ---
if len(df_filtrado) > 0 and len(coordenadores) > 0:
    df_status_coord = df_filtrado.groupby("COORDENADOR").apply(
        lambda x: pd.Series({
            "Pendentes": x["DATA_INSPECAO"].isna().sum(),
            "OK": x["DATA_INSPECAO"].notna().sum()
        })
    ).reset_index()

    df_status_coord["Total"] = df_status_coord["OK"] + df_status_coord["Pendentes"]
    df_status_coord["% OK"] = (df_status_coord["OK"] / df_status_coord["Total"] * 100).round(1)
    df_status_coord["% Pendentes"] = (df_status_coord["Pendentes"] / df_status_coord["Total"] * 100).round(1)

    df_melt = df_status_coord.melt(id_vars="COORDENADOR", value_vars=["% OK", "% Pendentes"],
                                  var_name="Status", value_name="Percentual")

    fig = px.bar(
        df_melt,
        x="COORDENADOR",
        y="Percentual",
        color="Status",
        color_discrete_map={"% OK": "#27ae60", "% Pendentes": "#f39c12"},
        labels={"Percentual": "% das Inspeções", "Status": "Status", "COORDENADOR": "Coordenador"},
        title="Percentual das Inspeções por Coordenador",
        text="Percentual"
    )
    fig.update_layout(barmode="stack", xaxis_tickangle=-45, yaxis=dict(range=[0,100]))
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Selecione um gerente e/ou coordenador para visualizar o gráfico.")

# --- TABELA INTERATIVA DOS PENDENTES ---
st.markdown("### Técnicos Pendentes")

colunas_exibir = ["TÉCNICO", "FUNCAO", "PRODUTO_SIMILAR", "SUPERVISOR", "SALDO SGM TÉCNICO"]
df_pendentes_display = df_pendentes[colunas_exibir].fillna("")

# JS para colorir a coluna SALDO SGM TÉCNICO
cell_style_jscode = JsCode("""
function(params) {
    if(params.value.toLowerCase().includes('não tem no saldo') || params.value.toLowerCase().includes('nao tem no saldo')){
        return {
            'color': '#721c24',
            'backgroundColor': '#f8d7da',
            'fontWeight': 'bold'
        }
    }
    if(params.value.toLowerCase().includes('tem no saldo')){
        return {
            'color': '#856404',
            'backgroundColor': '#fff3cd',
            'fontWeight': 'bold'
        }
    }
    return null;
};
""")

grid_builder = GridOptionsBuilder.from_dataframe(df_pendentes_display)
grid_builder.configure_columns(["SALDO SGM TÉCNICO"], cellStyle=cell_style_jscode)
gridOptions = grid_builder.build()

AgGrid(
    df_pendentes_display,
    gridOptions=gridOptions,
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    theme="fresh",
    height=400,
)
