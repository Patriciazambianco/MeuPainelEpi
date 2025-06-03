import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import io
import base64
import plotly.express as px
import json
import os
import hashlib

st.set_page_config(page_title="Inspeções EPI", layout="wide")

USUARIOS_JSON = "usuarios.json"

# ---------- Funções de hash para senha ----------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha, hash_salvo):
    return hash_senha(senha) == hash_salvo

# ---------- Carregar usuários salvos ----------
def carregar_usuarios():
    if os.path.exists(USUARIOS_JSON):
        with open(USUARIOS_JSON, "r") as f:
            return json.load(f)
    else:
        # Usuário default (pode mudar)
        return {
            "pati": hash_senha("minha_senha123")
        }

# ---------- Salvar usuários ----------
def salvar_usuarios(usuarios):
    with open(USUARIOS_JSON, "w") as f:
        json.dump(usuarios, f)

# ---------- Inicializa usuários ----------
usuarios = carregar_usuarios()

# ---------- Controla a tela atual (login ou cadastro) ----------
if 'modo' not in st.session_state:
    st.session_state['modo'] = 'login'
if 'usuario_logado' not in st.session_state:
    st.session_state['usuario_logado'] = None

# ---------- Função para carregar dados do GitHub ----------
@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

# ---------- Função para filtrar últimas inspeções ----------
def filtrar_ultimas_inspecoes_por_tecnico(df):
    df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")

    com_data = df[df["DATA_INSPECAO"].notna()]

    ultimas_por_tecnico = (
        com_data
        .sort_values("DATA_INSPECAO")
        .drop_duplicates(subset=["TÉCNICO"], keep="last")
    )

    tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
    sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)]

    sem_data_unicos = sem_data.drop_duplicates(subset=["TÉCNICO"])

    resultado = pd.concat([ultimas_por_tecnico, sem_data_unicos], ignore_index=True)

    return resultado

# ---------- Função para gerar link de download do Excel ----------
def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx" style="font-size:18px; color:#fff; background-color:#007acc; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Baixar Excel Tratado</a>'
    return href

# ---------- Estilo CSS customizado para KPIs ----------
kpi_css = """
<style>
.kpi-container {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 2rem;
}
.kpi-box {
    background-color: #007acc;
    color: white;
    border-radius: 10px;
    padding: 20px 30px;
    flex: 1;
    text-align: center;
    box-shadow: 0 4px 6px rgb(0 0 0 / 0.1);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.kpi-box.pending {
    background-color: #f39c12;
}
.kpi-box.percent {
    background-color: #27ae60;
}
.kpi-title {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
}
.kpi-value {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}
</style>
"""

# ---------- Menu lateral ----------
st.sidebar.title("Menu")

if st.session_state['usuario_logado']:
    opcao = st.sidebar.selectbox("Escolha uma opção:", ["Dashboard", "Sair"])
else:
    opcao = st.sidebar.selectbox("Escolha uma opção:", ["Login", "Cadastro"])

# ---------- Tela de Cadastro ----------
def tela_cadastro():
    st.title("🆕 Cadastro de Usuário")

    novo_usuario = st.text_input("Usuário")
    nova_senha = st.text_input("Senha", type="password")
    repetir_senha = st.text_input("Repita a senha", type="password")

    def cadastrar():
        if not novo_usuario or not nova_senha or not repetir_senha:
            st.error("Preencha todos os campos!")
            return
        if novo_usuario in usuarios:
            st.error("Usuário já existe!")
            return
        if nova_senha != repetir_senha:
            st.error("As senhas não coincidem!")
            return
        usuarios[novo_usuario] = hash_senha(nova_senha)
        salvar_usuarios(usuarios)
        st.success("Usuário criado com sucesso! Faça login agora.")
        st.session_state['modo'] = 'login'
        st.experimental_rerun()

    if st.button("Cadastrar"):
        cadastrar()

    if st.button("Já tenho conta / Voltar para Login"):
        st.session_state['modo'] = 'login'
        st.experimental_rerun()

# ---------- Tela de Login ----------
def tela_login():
    st.title("🔐 Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    def tentar_login():
        if usuario not in usuarios:
            st.error("Usuário não encontrado!")
            return False
        if not verificar_senha(senha, usuarios[usuario]):
            st.error("Senha incorreta!")
            return False
        return True

    if st.button("Entrar"):
        if tentar_login():
            st.session_state['usuario_logado'] = usuario
            st.success(f"Bem-vindo(a), {usuario}!")
            st.experimental_rerun()

    if st.button("Cadastrar nova conta"):
        st.session_state['modo'] = 'cadastro'
        st.experimental_rerun()

# ---------- Tela Dashboard ----------
def tela_dashboard():
    st.title(f"🦺 Painel de Inspeções EPI - Usuário: {st.session_state['usuario_logado']}")
    if st.button("Sair"):
        st.session_state['usuario_logado'] = None
        st.experimental_rerun()

    # Carrega e trata os dados
    df_raw = carregar_dados()
    df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

    # Filtros
    col1, col2 = st.columns(2)
    gerentes = df_tratado["GERENTE"].dropna().unique()
    coordenadores = df_tratado["COORDENADOR"].dropna().unique()

    with col1:
        gerente_sel = st.multiselect("Filtrar por Gerente", sorted(gerentes))
    with col2:
        coordenador_sel = st.multiselect("Filtrar por Coordenador", sorted(coordenadores))

    df_filtrado = df_tratado.copy()
    if gerente_sel:
        df_filtrado = df_filtrado[df_filtrado["GERENTE"].isin(gerente_sel)]
    if coordenador_sel:
        df_filtrado = df_filtrado[df_filtrado["COORDENADOR"].isin(coordenador_sel)]

    # KPIs
    total = len(df_filtrado)
    pending = df_filtrado["DATA_INSPECAO"].isna().sum()
    ok = total - pending
    pct_ok = round(ok / total * 100, 1) if total > 0 else 0
    pct_pendente = round(100 - pct_ok, 1)

    # Aplica o CSS e monta os KPIs coloridos via HTML
    st.markdown(kpi_css, unsafe_allow_html=True)

    kpis_html = f"""
    <div class="kpi-container">
        <div class="kpi-box percent">
            <div class="kpi-title">Inspeções OK</div>
            <div class="kpi-value">{ok}</div>
        </div>
        <div class="kpi-box pending">
            <div class="kpi-title">Pendentes</div>
            <div class="kpi-value">{pending}</div>
        </div>
        <div class="kpi-box percent">
            <div class="kpi-title">% OK</div>
            <div class="kpi-value">{pct_ok}%</div>
        </div>
        <div class="kpi-box pending">
            <div class="kpi-title">% Pendentes</div>
            <div class="kpi-value">{pct_pendente}%</div>
        </div>
    </div>
    """

    st.markdown(kpis_html, unsafe_allow_html=True)

    # Gráfico de pizza simples das inspeções OK vs Pendentes
    fig = px.pie(
        names=["OK", "Pendentes"],
        values=[ok, pending],
        color=["OK", "Pendentes"],
        color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"},
        title="Status das Inspeções"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabela dos dados filtrados
    st.dataframe(df_filtrado)

    # Link para download do Excel tratado
    st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)

# ---------- Roda a aplicação ----------
if st.session_state['modo'] == 'login' and not st.session_state['usuario_logado']:
    tela_login()
elif st.session_state['modo'] == 'cadastro' and not st.session_state['usuario_logado']:
    tela_cadastro()
elif st.session_state['usuario_logado']:
    tela_dashboard()
else:
    st.error("Erro inesperado no estado do app. Reinicie a página.")
