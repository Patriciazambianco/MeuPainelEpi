import streamlit as st
import pandas as pd
import io
import base64
import plotly.express as px
import streamlit_authenticator as stauth

st.set_page_config(page_title="Inspeções EPI", layout="wide", initial_sidebar_state="collapsed")

# --- Se o nome for "pati", pula o login ---
Patricia Zambianco_auto_login = True

if pati_auto_login:
    username = "Patricia Zambianco"
    name = "Patricia Zambianco"
    authentication_status = True
else:
    # --- Usuários e senhas (só os outros fazem login) ---
    users = {
        "usernames": {
            "coordenador": {
                "name": "Coordenador",
                "password": stauth.Hasher(['senhaCoord456']).generate()[0]
            },
        }
    }

    authenticator = stauth.Authenticate(
        users['usernames'],
        "cookie_meupainelepi",
        "chave_secreta_meupainel",
        cookie_expiry_days=1
    )

    name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    if username != "pati":
        authenticator.logout('Sair', 'main')

    st.write(f"👋 Bem-vindo(a), {name}!")

    # --- Carrega dados do GitHub ---
    @st.cache_data
    def carregar_dados():
        url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%83O%20EPI.xlsx"
        return pd.read_excel(url, engine="openpyxl")

    def filtrar_ultimas_inspecoes_por_tecnico(df):
        df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
        com_data = df[df["DATA_INSPECAO"].notna()]
        ultimas = com_data.sort_values("DATA_INSPECAO").drop_duplicates(subset=["TÉCNICO"], keep="last")
        tecnicos_com_data = ultimas["TÉCNICO"].unique()
        sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_data)].drop_duplicates(subset=["TÉCNICO"])
        return pd.concat([ultimas, sem_data], ignore_index=True)

    def gerar_download_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
        b64 = base64.b64encode(output.getvalue()).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx">📥 Baixar Excel</a>'

    kpi_css = """
    <style>
    .kpi-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .kpi-box {
        background-color: #007acc;
        color: white;
        border-radius: 10px;
        padding: 20px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 6px rgb(0 0 0 / 0.1);
    }
    .kpi-box.pending { background-color: #f39c12; }
    .kpi-box.percent { background-color: #27ae60; }
    .kpi-title { font-size: 1rem; margin-bottom: 0.5rem; font-weight: 600; }
    .kpi-value { font-size: 2rem; font-weight: 700; }
    </style>
    """

    st.title("🦺 Painel de Inspeções EPI")
    st.markdown(kpi_css, unsafe_allow_html=True)

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

    total = len(df_filtrado)
    pendentes = df_filtrado["DATA_INSPECAO"].isna().sum()
    ok = total - pendentes
    pct_ok = round(ok / total * 100, 1) if total > 0 else 0
    pct_pend = 100 - pct_ok

    kpis_html = f"""
    <div class="kpi-container">
        <div class="kpi-box percent"><div class="kpi-title">Inspeções OK</div><div class="kpi-value">{ok}</div></div>
        <div class="kpi-box pending"><div class="kpi-title">Pendentes</div><div class="kpi-value">{pendentes}</div></div>
        <div class="kpi-box percent"><div class="kpi-title">% OK</div><div class="kpi-value">{pct_ok}%</div></div>
        <div class="kpi-box pending"><div class="kpi-title">% Pendentes</div><div class="kpi-value">{pct_pend}%</div></div>
    </div>
    """
    st.markdown(kpis_html, unsafe_allow_html=True)

    fig = px.pie(
        names=["OK", "Pendentes"],
        values=[ok, pendentes],
        title="Status das Inspeções",
        color=["OK", "Pendentes"],
        color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico por coordenador
    status_coord = df_filtrado.groupby(["COORDENADOR", df_filtrado["DATA_INSPECAO"].notna()])\
        .size().unstack(fill_value=0).rename(columns={True: "OK", False: "Pendentes"}).reset_index()
    status_coord["Total"] = status_coord["OK"] + status_coord["Pendentes"]
    status_coord["% OK"] = status_coord["OK"] / status_coord["Total"] * 100

    if not status_coord.empty:
        fig2 = px.bar(
            status_coord,
            x="COORDENADOR",
            y="% OK",
            title="% OK por Coordenador",
            text=status_coord["% OK"].apply(lambda x: f"{x:.1f}%"),
            color="% OK",
            color_continuous_scale=px.colors.sequential.Mint
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # Tabela e botão de download
    st.markdown("### Dados Tratados")
    st.dataframe(df_filtrado, use_container_width=True)
    st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)

elif authentication_status == False:
    st.error('Usuário ou senha inválidos')
elif authentication_status is None:
    st.warning('Por favor, faça login')
