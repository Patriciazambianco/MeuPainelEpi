import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import io
import base64
import plotly.express as px

st.set_page_config(page_title="Inspeções EPI", layout="wide")

# --- Verifica se o usuário é "pati" e pula autenticação ---
query_params = st.experimental_get_query_params()
pati_auto_login = "pati" in query_params.get("user", [])

if not pati_auto_login:
    # Usuários e senhas
    users = {
        "usernames": {
            "pati": {"name": "Pati", "password": stauth.Hasher(["senha_qualquer"]).generate()[0]},
            "coordenador": {"name": "Coordenador", "password": stauth.Hasher(["senhaCoord456"]).generate()[0]}
        }
    }
    
    authenticator = stauth.Authenticate(
        users["usernames"],
        "cookie_meupainelepi",
        "chave_secreta_meupainel",
        cookie_expiry_days=1
    )

    name, authentication_status, username = authenticator.login("Login", "main")
else:
    name = "Pati"
    authentication_status = True

if pati_auto_login or authentication_status:
    if not pati_auto_login:
        authenticator.logout("Sair", "main")
    st.write(f"👋 Bem-vindo(a), {name}!")

    @st.cache_data
    def carregar_dados():
        url = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"
        df = pd.read_excel(url, engine="openpyxl")
        return df

    def filtrar_ultimas_inspecoes_por_tecnico(df):
        df["DATA_INSPECAO"] = pd.to_datetime(df["DATA_INSPECAO"], errors="coerce")
        com_data = df[df["DATA_INSPECAO"].notna()]
        ultimas_por_tecnico = com_data.sort_values("DATA_INSPECAO").drop_duplicates("TÉCNICO", keep="last")
        tecnicos_com_inspecao = ultimas_por_tecnico["TÉCNICO"].unique()
        sem_data = df[~df["TÉCNICO"].isin(tecnicos_com_inspecao)].drop_duplicates("TÉCNICO")
        return pd.concat([ultimas_por_tecnico, sem_data], ignore_index=True)

    def gerar_download_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="InspecoesTratadas")
        dados_excel = output.getvalue()
        b64 = base64.b64encode(dados_excel).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="inspecoes_tratadas.xlsx" style="font-size:18px; color:#fff; background-color:#007acc; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Baixar Excel Tratado</a>'

    st.markdown("<style>.block-container{padding-top:2rem}</style>", unsafe_allow_html=True)
    st.title("🦺 Painel de Inspeções EPI")

    df_raw = carregar_dados()
    df_tratado = filtrar_ultimas_inspecoes_por_tecnico(df_raw)

    gerentes = df_tratado["GERENTE"].dropna().unique()
    coordenadores = df_tratado["COORDENADOR"].dropna().unique()

    col1, col2 = st.columns(2)
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
    pending = df_filtrado["DATA_INSPECAO"].isna().sum()
    ok = total - pending
    pct_ok = round(ok / total * 100, 1) if total > 0 else 0
    pct_pendente = round(100 - pct_ok, 1)

    st.markdown("""
        <style>
        .kpi-container {display: flex; gap: 1.5rem; margin-bottom: 2rem;}
        .kpi-box {background-color: #007acc; color: white; border-radius: 10px; padding: 20px 30px; flex: 1; text-align: center; box-shadow: 0 4px 6px rgb(0 0 0 / 0.1); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
        .kpi-box.pending {background-color: #f39c12;}
        .kpi-box.percent {background-color: #27ae60;}
        .kpi-title {font-size: 1.1rem; margin-bottom: 0.5rem; font-weight: 600;}
        .kpi-value {font-size: 2.5rem; font-weight: 700; line-height: 1;}
        </style>
    """, unsafe_allow_html=True)

    kpis_html = f"""
    <div class="kpi-container">
        <div class="kpi-box percent"><div class="kpi-title">Inspeções OK</div><div class="kpi-value">{ok}</div></div>
        <div class="kpi-box pending"><div class="kpi-title">Pendentes</div><div class="kpi-value">{pending}</div></div>
        <div class="kpi-box percent"><div class="kpi-title">% OK</div><div class="kpi-value">{pct_ok}%</div></div>
        <div class="kpi-box pending"><div class="kpi-title">% Pendentes</div><div class="kpi-value">{pct_pendente}%</div></div>
    </div>
    """
    st.markdown(kpis_html, unsafe_allow_html=True)

    fig = px.pie(
        names=["OK", "Pendentes"],
        values=[ok, pending],
        title="Status das Inspeções",
        color=["OK", "Pendentes"],
        color_discrete_map={"OK": "#27ae60", "Pendentes": "#f39c12"}
    )
    st.plotly_chart(fig, use_container_width=True)

    status_por_coord = (
        df_filtrado
        .groupby(["COORDENADOR", df_filtrado["DATA_INSPECAO"].notna()])
        .size()
        .unstack(fill_value=0)
        .rename(columns={True: "OK", False: "Pendentes"})
        .reset_index()
    )
    status_por_coord["Total"] = status_por_coord["OK"] + status_por_coord["Pendentes"]
    status_por_coord["% OK"] = (status_por_coord["OK"] / status_por_coord["Total"]) * 100

    if not status_por_coord.empty and status_por_coord["Total"].sum() > 0:
        fig2 = px.bar(
            status_por_coord,
            x="COORDENADOR",
            y="% OK",
            title="% Inspeções OK por Coordenador",
            labels={"% OK": "% Inspeções OK", "COORDENADOR": "Coordenador"},
            text=status_por_coord["% OK"].apply(lambda x: f"{x:.1f}%"),
            color="% OK",
            color_continuous_scale=px.colors.sequential.Mint
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o gráfico de coordenadores.")

    st.markdown("### Dados Tratados")
    st.dataframe(df_filtrado, use_container_width=True)
    st.markdown(gerar_download_excel(df_filtrado), unsafe_allow_html=True)

elif not pati_auto_login:
    if authentication_status is False:
        st.error('Usuário ou senha inválidos')
    elif authentication_status is None:
        st.warning('Por favor, faça login')
