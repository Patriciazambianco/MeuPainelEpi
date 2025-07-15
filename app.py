import streamlit as st
import pandas as pd
from io import BytesIO

# Configura a página
st.set_page_config(page_title="Painel de Inspeções EPI", layout="wide")

# Função para gerar arquivo Excel para download
def gerar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pendentes')
    output.seek(0)
    return output

# Link RAW do seu arquivo no GitHub
url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# Lê o Excel
df = pd.read_excel(url)

# Mostra os dados crus (opcional para debug)
# st.dataframe(df)

# --- AJUSTE NOMES DAS COLUNAS CONFORME NECESSÁRIO ---
# Exemplo esperado: "TECNICO", "GERENTE", "COORDENADOR", "STATUS"
# Renomeie se necessário:
df = df.rename(columns=lambda x: x.upper().strip())
df = df.rename(columns={
    "SITUAÇÃO_TECNICO": "STATUS",  # adapte conforme necessário
    "COORDENADOR": "COORDENADOR",
    "GERENTE": "GERENTE",
    "TECNICO": "TECNICO"
})

# Filtros
col1, col2 = st.columns(2)
gerentes = sorted(df['GERENTE'].dropna().unique().tolist())
coordenadores = sorted(df['COORDENADOR'].dropna().unique().tolist())

with col1:
    gerente_selecionado = st.selectbox("Filtrar por GERENTE:", ["Todos"] + gerentes)
with col2:
    coordenador_selecionado = st.selectbox("Filtrar por COORDENADOR:", ["Todos"] + coordenadores)

# Aplicar filtros
df_filtrado = df.copy()
if gerente_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["GERENTE"] == gerente_selecionado]
if coordenador_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["COORDENADOR"] == coordenador_selecionado]

# Agrupar por técnico e status
tabela_tecnicos = df_filtrado.groupby(["TECNICO", "STATUS"]).size().unstack(fill_value=0)
tabela_tecnicos["Tem_OK"] = tabela_tecnicos.get("OK", 0) > 0
tabela_tecnicos["Tem_Pendente"] = tabela_tecnicos.get("PENDENTE", 0) > 0

# KPIs
ok = tabela_tecnicos["Tem_OK"].sum()
pendentes = tabela_tecnicos["Tem_Pendente"].sum()
total = tabela_tecnicos.shape[0]
pct_ok = round(ok / total * 100, 1) if total > 0 else 0
pct_pend = round(pendentes / total * 100, 1) if total > 0 else 0

# Exibir KPIs
st.markdown(f"""
<style>
.kpi-container {{
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.kpi-box {{
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 12px;
    font-size: 24px;
    font-weight: bold;
    text-align: center;
    min-width: 200px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}}
.green {{ background-color: #d4edda; color: #155724; }}
.orange {{ background-color: #fff3cd; color: #856404; }}
</style>

<div class="kpi-container">
  <div class="kpi-box green">✔️ Técnicos com OK: {ok}</div>
  <div class="kpi-box orange">⚠️ Técnicos Pendentes: {pendentes}</div>
  <div class="kpi-box green">✅ % Técnicos OK: {pct_ok}%</div>
  <div class="kpi-box orange">❌ % Técnicos Pendentes: {pct_pend}%</div>
</div>
""", unsafe_allow_html=True)

# Técnicos Pendentes
tecnicos_pendentes = tabela_tecnicos[tabela_tecnicos["Tem_Pendente"] == True].reset_index()
df_pendentes = pd.merge(tecnicos_pendentes[["TECNICO"]], df_filtrado, on="TECNICO", how="left")

with st.expander("📋 Ver Técnicos Pendentes"):
    st.dataframe(df_pendentes)

# Botão para baixar Excel dos Pendentes
excel_download = gerar_excel_download(df_pendentes)
st.download_button(
    label="⬇️ Baixar Pendentes em Excel",
    data=excel_download,
    file_name="pendentes_tecnicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
