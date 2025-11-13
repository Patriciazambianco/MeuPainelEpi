import streamlit as st
import pandas as pd
import plotly.express as px

# 🎨 CONFIGURAÇÃO GERAL
st.set_page_config(page_title="Check List EPI - Técnicos OK/Pendentes", layout="wide")

# 💅 CSS personalizado
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #f8fbff, #f3e5f5);
    }
    h1 {
        text-align: center;
        color: #1b5e20;
        font-weight: 800;
        font-size: 2.2rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 13px;
        border-radius: 13px;
        color: white;
        font-weight: bold;
        text-align: center;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: scale(1.05);
    }
    .ok-card {background: linear-gradient(135deg, #2ecc71, #27ae60);}
    .pendente-card {background: linear-gradient(135deg, #e74c3c, #c0392b);}
    </style>
""", unsafe_allow_html=True)

# 🧠 TÍTULO
st.title("🦺 Check List EPI - Técnicos OK e Pendentes")

# 🚀 FUNÇÃO DE CARGA E PADRONIZAÇÃO
@st.cache_data
def carregar_dados(url):
    df = pd.read_excel(url)
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    if "STATUS_CHECK_LIST" in df.columns:
        df["STATUS_CHECK_LIST"] = (
            df["STATUS_CHECK_LIST"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "CHECK LIST OK": "OK",
                "CHECKLIST OK": "OK",
                "OK": "OK",
                "PENDENTE": "PENDENTE"
            })
        )
    else:
        st.warning("⚠️ A coluna 'STATUS_CHECK_LIST' não existe na base. Todos foram marcados como 'PENDENTE'.")
        df["STATUS_CHECK_LIST"] = "PENDENTE"

    return df

# 🔗 URL DO ARQUIVO
url = "https://github.com/Patriciazambianco/MeuPainelEpi/raw/main/LISTA%20DE%20VERIFICA%C3%87%C3%83O%20EPI.xlsx"

# 🧩 CARREGAMENTO
df = carregar_dados(url)

# 📊 MÉTRICAS GERAIS
total = len(df)
qtd_ok = (df["STATUS_CHECK_LIST"] == "OK").sum()
qtd_pend = (df["STATUS_CHECK_LIST"] == "PENDENTE").sum()
perc_ok = round((qtd_ok / total) * 100, 1) if total > 0 else 0
perc_pend = round((qtd_pend / total) * 100, 1) if total > 0 else 0

# 🎯 MÉTRICAS COLORIDAS
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class='metric-card ok-card'>
        <h3>✅ % OK</h3>
        <h2>{perc_ok:.1f}%</h2>
        <p>{qtd_ok} de {total}</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class='metric-card pendente-card'>
        <h3>⚠️ % Pendentes</h3>
        <h2>{perc_pend:.1f}%</h2>
        <p>{qtd_pend} de {total}</p>
    </div>
    """, unsafe_allow_html=True)

# 📈 FUNÇÃO PARA GRÁFICO DE % POR GRUPO
def grafico_percentual(df, grupo, titulo):
    cont = (
        df.groupby([grupo, "STATUS_CHECK_LIST"])["TECNICO"]
        .nunique()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["OK", "PENDENTE"]:
        if col not in cont.columns:
            cont[col] = 0

    cont["TOTAL"] = cont["OK"] + cont["PENDENTE"]
    cont["% OK"] = (cont["OK"] / cont["TOTAL"] * 100).round(1)
    cont["% PENDENTE"] = (cont["PENDENTE"] / cont["TOTAL"] * 100).round(1)

    df_bar = cont.melt(
        id_vars=[grupo],
        value_vars=["% OK", "% PENDENTE"],
        var_name="STATUS",
        value_name="PERCENTUAL"
    )
    df_bar["STATUS"] = df_bar["STATUS"].str.replace("% ", "")

    fig = px.bar(
        df_bar,
        x=grupo,
        y="PERCENTUAL",
        color="STATUS",
        color_discrete_map={"OK": "#2ecc71", "PENDENTE": "#e74c3c"},
        text=df_bar["PERCENTUAL"].apply(lambda x: f"{x:.1f}%"),
        barmode="group",
        title=titulo
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Percentual (%)",
        xaxis=dict(categoryorder="total descending"),
        title_font=dict(size=18, color="#1b5e20")
    )
    return fig

# 📊 GRÁFICOS POR GERENTE E COORDENADOR
if "GERENTE" in df.columns:
    st.plotly_chart(
        grafico_percentual(df, "GERENTE", "📈 Técnicos OK x Pendentes por Gerente"),
        use_container_width=True
    )
else:
    st.warning("⚠️ Coluna 'GERENTE' não encontrada na base.")

if "COORDENADOR" in df.columns:
    st.plotly_chart(
        grafico_percentual(df, "COORDENADOR", "📊 Técnicos OK x Pendentes por Coordenador"),
        use_container_width=True
    )
else:
    st.warning("⚠️ Coluna 'COORDENADOR' não encontrada na base.")

# 📋 PRÉVIA DOS DADOS
st.markdown("### 📋 Prévia dos Dados")
st.dataframe(df.head())
