import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Painel Inspeções EPI", layout="wide")

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    
    # Confirma se coluna existe
    if "SALDO SGM TÉCNICO" in df.columns:
        # Troca NaN, espaços e '' por "Não tem no saldo"
        df["SALDO SGM TÉCNICO"] = df["SALDO SGM TÉCNICO"].fillna("").astype(str).str.strip()
        df.loc[df["SALDO SGM TÉCNICO"] == "", "SALDO SGM TÉCNICO"] = "Não tem no saldo"
    else:
        st.error("Coluna 'SALDO SGM TÉCNICO' não encontrada na planilha.")
        df["SALDO SGM TÉCNICO"] = "Não tem no saldo"
        
    return df

def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
    com_data = df[df["DATA_INSPECAO"].notna()]
    ultimas_por_tecnico = (
        com_data.sort_values("DATA_INSPECAO")
        .drop_duplicates(subset=["TÉCNICO"], keep="last")
    )
    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]
    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])
    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)
    return resultado

def destacar_saldo(val):
    val_lower = val.lower()
    if "não tem no saldo" in val_lower or "nao tem no saldo" in val_lower:
        return 'background-color: #f8d7da; color: #721c24;'  # vermelho clarinho
    elif "tem no saldo" in val_lower:
        return 'background-color: #fff3cd; color: #856404;'  # amarelo clarinho
    else:
        return ''

st.title("🦺 Painel de Inspeções EPI")

df_raw = carregar_dados()
df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

gerentes = sorted(df_tratado["GERENTE"].dropna().unique())
gerente_sel = st.selectbox("Filtrar por Gerente", ["-- Todos --"] + gerentes)

if gerente_sel != "-- Todos --":
    df_filtrado_ger = df_tratado[df_tratado["GERENTE"] == gerente_sel]
else:
    df_filtrado_ger = df_tratado.copy()

coordenadores = sorted(df_filtrado_ger["COORDENADOR"].dropna().unique())
coordenador_sel = st.multiselect("Filtrar por Coordenador", coordenadores)

df_filtrado = df_filtrado_ger.copy()
if coordenador_sel:
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

# KPIs etc (pode adicionar aqui igual no código anterior)...

df_pendentes = df_filtrado[df_filtrado["DATA_INSPECAO"].isna()]
colunas_tabela = ["TÉCNICO", "SUPERVISOR", "SALDO SGM TÉCNICO"]
df_pendentes_clean = df_pendentes[colunas_tabela].fillna("").astype(str)

st.markdown("### Técnicos Pendentes com Status do Saldo SGM")
st.write(
    df_pendentes_clean.style
    .applymap(destacar_saldo, subset=["SALDO SGM TÉCNICO"])
    .hide(axis="index")
)
