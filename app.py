import streamlit as st
import hashlib
import json
import os
import pandas as pd
import io
import base64
import plotly.express as px

USERS_FILE = "usuarios.json"

def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USERS_FILE, "w") as f:
        json.dump(usuarios, f)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
    dados_excel = output.getvalue()
    b64 = base64.b64encode(dados_excel).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx" style="font-size:18px; color:#fff; background-color:#007acc; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Baixar Excel Tratado</a>'
    return href

@st.cache_data
def carregar_dados():
    url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
    df = pd.read_excel(url, engine="openpyxl")
    return df

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

# Inicializa o estado de autenticação
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario_logado' not in st.session_state:
    st.session_state['usuario_logado'] = ""

st.title("🦺 Painel de Inspeções EPI")

# Carregar usuários cadastrados
usuarios = carregar_usuarios()

# Menu lateral
menu = st.sidebar.selectbox("Menu", ["Login", "Cadastro", "Sair"])

if menu == "Cadastro":
    st.header("Crie sua conta")
    novo_usuario = st.text_input("Usuário", key="cadastro_usuario")
    nova_senha = st.text_input("Senha", type="password", key="cadastro_senha")
    repetir_senha = st.text_input("Repita a senha", type="password", key="cadastro_repetir_senha")

    if st.button("Cadastrar"):
        if novo_usuario.strip() == "" or nova_senha.strip() == "":
            st.error("Por favor, preencha todos os campos.")
        elif novo_usuario in usuarios:
            st.error("Usuário já existe, escolha outro nome.")
        elif nova_senha != repetir_senha:
            st.error("As senhas não coincidem.")
        else:
            usuarios[novo_usuario] = hash_senha(nova_senha)
            salvar_usuarios(usuarios)
            st.success("Usuário cadastrado com sucesso! Agora faça login.")
            st.experimental_rerun()  # Atualiza página para trocar para login automaticamente

elif menu == "Login":
    st.header("Faça seu login")
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")

    if st.button("Entrar"):
        if usuario in usuarios and usuarios[usuario] == hash_senha(senha):
            st.success(f"Bem-vindo(a), {usuario}!")
            st.session_state['autenticado'] = True
            st.session_state['usuario_logado'] = usuario
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos!")

elif menu == "Sair":
    st.session_state['autenticado'] = False
    st.session_state['usuario_logado'] = ""
    st.info("Você saiu do sistema.")

# Se autenticado, mostra o painel
if st.session_state['autenticado']:
    st.sidebar.write(f"👤 Logado como: **{st.session_state['usuario_logado']}**")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({'autenticado': False, 'usuario_logado': ""}) or st.experimental_rerun())

    # Seu código do painel EPI aqui:

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

    # Gráfico pizza
    fig = px.pie(
        names=["OK", "Pendentes"],
        values=[ok, pending],
        title="Status das Inspeções",
        color=["OK", "Pendentes"],
        color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico % por Coordenador
    if not df_filtrado.empty:
        df_agg = (
            df_filtrado.groupby("COORDENADOR")["DATA_INSPECAO"]
            .apply(lambda x: x.notna().mean() * 100)
            .reset_index()
            .rename(columns={"DATA_INSPECAO": "% Inspeções OK"})
            .sort_values("% Inspeções OK", ascending=False)
        )
        fig2 = px.bar(
            df_agg,
            x="COORDENADOR",
            y="% Inspeções OK",
            title="% Inspeções OK por Coordenador",
            labels={"COORDENADOR": "Coordenador", "% Inspeções OK": "% OK"},
            color="% Inspeções OK",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Mostrar tabela filtrada
    st.dataframe(df_filtrado.reset_index(drop=True))

    # Botão para baixar Excel tratado
    st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)

else:
    st.info("Faça login ou crie uma conta para acessar o painel.")
