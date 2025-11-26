import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Painel Check List EPI", layout="wide")
st.title("🦺 Painel Check List EPI")

# =========================
# CARREGAMENTO DO EXCEL
# =========================

URL = "https://raw.githubusercontent.com/Patriciazambianco/MeuPainelEpi/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.astype(str).str.upper().str.strip().str.replace(" ", "_")

    # Normalização
    if "STATUS_CHECK_LIST" not in df.columns:
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    df["STATUS_CHECK_LIST"] = (
        df["STATUS_CHECK_LIST"].astype(str).str.upper().str.strip().replace({
            "CHECK LIST OK": "OK",
            "CHECKLIST OK": "OK",
            "OK": "OK",
            "PENDENTE": "PENDENTE"
        })
    )

    # Colunas protegidas
    for col in ["TECNICO", "GERENTE", "COORDENADOR", "PRODUTO_SIMILAR"]:
        if col not in df.columns:
            df[col] = None

    return df


try:
    df = carregar_dados(URL)
except Exception as e:
    st.error("Erro ao carregar arquivo do GitHub.")
    st.exception(e)
    st.stop()


# =========================
# SIDEBAR
# =========================
st.sidebar.header("🎯 Filtros")
gerentes = ["Todos"] + sorted(df["GERENTE"].dropna().unique().tolist())
coords = ["Todos"] + sorted(df["COORDENADOR"].dropna().unique().tolist())

g_sel = st.sidebar.selectbox("Gerente", gerentes)
c_sel = st.sidebar.selectbox("Coordenador", coords)

df_f = df.copy()

if g_sel != "Todos":
    df_f = df_f[df_f["GERENTE"] == g_sel]
if c_sel != "Todos":
    df_f = df_f[df_f["COORDENADOR"] == c_sel]


# =========================
# MÉTRICAS
# =========================
total = len(df_f)
ok = int((df_f["STATUS_CHECK_LIST"] == "OK").sum())
pend = int((df_f["STATUS_CHECK_LIST"] == "PENDENTE").sum())

p_ok = round(ok / total * 100, 1) if total else 0
p_pend = round(pend / total * 100, 1) if total else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✔ OK", ok)
c2.metric("⚠ Pendentes", pend)
c3.metric("% OK", f"{p_ok}%")
c4.metric("% Pendentes", f"{p_pend}%")


st.markdown("---")


# =========================
# FUNÇÃO PLOTLY (GRÁFICOS MENORES)
# =========================
def graf_pizza_plotly(ok_value, pend_value, titulo):
    fig = px.pie(
        values=[ok_value, pend_value],
        names=["OK", "PENDENTE"],
        title=titulo,
        hole=0.4,
    )

    fig.update_traces(
        textinfo="percent+label",
        textfont_size=12,
        pull=[0.05, 0],
    )

    fig.update_layout(
        height=260,   # 🔥 menor
        width=260,
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig


# =========================
# GRÁFICOS GERAIS
# =========================
colA, colB, colC = st.columns(3)

with colA:
    st.plotly_chart(graf_pizza_plotly(ok, pend, "Status Geral"), use_container_width=False)

# GRÁFICO POR GERENTE
cont_g = df_f.groupby(["GERENTE", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
if "OK" not in cont_g: cont_g["OK"] = 0
if "PENDENTE" not in cont_g: cont_g["PENDENTE"] = 0

if g_sel == "Todos" and not cont_g.empty:
    g_ok = cont_g["OK"].sum()
    g_p = cont_g["PENDENTE"].sum()

    with colB:
        st.plotly_chart(
            graf_pizza_plotly(g_ok, g_p, "Gerentes"),
            use_container_width=False
        )


# GRÁFICO POR COORDENADOR
cont_c = df_f.groupby(["COORDENADOR", "STATUS_CHECK_LIST"])["TECNICO"].nunique().unstack(fill_value=0).reset_index()
if "OK" not in cont_c: cont_c["OK"] = 0
if "PENDENTE" not in cont_c: cont_c["PENDENTE"] = 0

if c_sel == "Todos" and not cont_c.empty:
    c_ok = cont_c["OK"].sum()
    c_p = cont_c["PENDENTE"].sum()

    with colC:
        st.plotly_chart(
            graf_pizza_plotly(c_ok, c_p, "Coordenadores"),
            use_container_width=False
        )


st.markdown("---")


# =========================
# TABELA DE PENDENTES + DOWNLOAD
# =========================
pendentes = df_f[df_f["STATUS_CHECK_LIST"] == "PENDENTE"]

st.subheader("📋 Técnicos Pendentes")
cols_safe = ["TECNICO", "PRODUTO_SIMILAR", "COORDENADOR", "GERENTE", "STATUS_CHECK_LIST"]
cols_safe = [c for c in cols_safe if c in pendentes.columns]

st.dataframe(pendentes[cols_safe])

if not pendentes.empty:
    output = BytesIO()
    pendentes.to_excel(output, index=False, sheet_name="Pendentes")
    st.download_button(
        "📥 Baixar Pendentes",
        output.getvalue(),
        file_name="Pendentes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.success("Nenhum pendente. Tudo lindo 😎")
