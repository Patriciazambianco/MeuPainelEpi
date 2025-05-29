{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "mount_file_id": "1HctDrwGuGYG4awnq4o7qopdFXYxCVRiU",
      "authorship_tag": "ABX9TyOsD+4Xzjbzl0VsgiLma32X",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Patriciazambianco/MeuPainelEpi/blob/main/app.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "pip install streamlit pandas plotly openpyxl\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "__e0Gj83xfEe",
        "outputId": "61a95d01-bd64-42e9-c445-b57e7b7c2a61"
      },
      "execution_count": 1,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "Collecting streamlit\n",
            "  Downloading streamlit-1.45.1-py3-none-any.whl.metadata (8.9 kB)\n",
            "Requirement already satisfied: pandas in /usr/local/lib/python3.11/dist-packages (2.2.2)\n",
            "Requirement already satisfied: plotly in /usr/local/lib/python3.11/dist-packages (5.24.1)\n",
            "Requirement already satisfied: openpyxl in /usr/local/lib/python3.11/dist-packages (3.1.5)\n",
            "Requirement already satisfied: altair<6,>=4.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (5.5.0)\n",
            "Requirement already satisfied: blinker<2,>=1.5.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (1.9.0)\n",
            "Requirement already satisfied: cachetools<6,>=4.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (5.5.2)\n",
            "Requirement already satisfied: click<9,>=7.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (8.2.1)\n",
            "Requirement already satisfied: numpy<3,>=1.23 in /usr/local/lib/python3.11/dist-packages (from streamlit) (2.0.2)\n",
            "Requirement already satisfied: packaging<25,>=20 in /usr/local/lib/python3.11/dist-packages (from streamlit) (24.2)\n",
            "Requirement already satisfied: pillow<12,>=7.1.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (11.2.1)\n",
            "Requirement already satisfied: protobuf<7,>=3.20 in /usr/local/lib/python3.11/dist-packages (from streamlit) (5.29.4)\n",
            "Requirement already satisfied: pyarrow>=7.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (18.1.0)\n",
            "Requirement already satisfied: requests<3,>=2.27 in /usr/local/lib/python3.11/dist-packages (from streamlit) (2.32.3)\n",
            "Requirement already satisfied: tenacity<10,>=8.1.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (9.1.2)\n",
            "Requirement already satisfied: toml<2,>=0.10.1 in /usr/local/lib/python3.11/dist-packages (from streamlit) (0.10.2)\n",
            "Requirement already satisfied: typing-extensions<5,>=4.4.0 in /usr/local/lib/python3.11/dist-packages (from streamlit) (4.13.2)\n",
            "Collecting watchdog<7,>=2.1.5 (from streamlit)\n",
            "  Downloading watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl.metadata (44 kB)\n",
            "\u001b[2K     \u001b[90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m \u001b[32m44.3/44.3 kB\u001b[0m \u001b[31m1.5 MB/s\u001b[0m eta \u001b[36m0:00:00\u001b[0m\n",
            "\u001b[?25hRequirement already satisfied: gitpython!=3.1.19,<4,>=3.0.7 in /usr/local/lib/python3.11/dist-packages (from streamlit) (3.1.44)\n",
            "Collecting pydeck<1,>=0.8.0b4 (from streamlit)\n",
            "  Downloading pydeck-0.9.1-py2.py3-none-any.whl.metadata (4.1 kB)\n",
            "Requirement already satisfied: tornado<7,>=6.0.3 in /usr/local/lib/python3.11/dist-packages (from streamlit) (6.4.2)\n",
            "Requirement already satisfied: python-dateutil>=2.8.2 in /usr/local/lib/python3.11/dist-packages (from pandas) (2.9.0.post0)\n",
            "Requirement already satisfied: pytz>=2020.1 in /usr/local/lib/python3.11/dist-packages (from pandas) (2025.2)\n",
            "Requirement already satisfied: tzdata>=2022.7 in /usr/local/lib/python3.11/dist-packages (from pandas) (2025.2)\n",
            "Requirement already satisfied: et-xmlfile in /usr/local/lib/python3.11/dist-packages (from openpyxl) (2.0.0)\n",
            "Requirement already satisfied: jinja2 in /usr/local/lib/python3.11/dist-packages (from altair<6,>=4.0->streamlit) (3.1.6)\n",
            "Requirement already satisfied: jsonschema>=3.0 in /usr/local/lib/python3.11/dist-packages (from altair<6,>=4.0->streamlit) (4.23.0)\n",
            "Requirement already satisfied: narwhals>=1.14.2 in /usr/local/lib/python3.11/dist-packages (from altair<6,>=4.0->streamlit) (1.40.0)\n",
            "Requirement already satisfied: gitdb<5,>=4.0.1 in /usr/local/lib/python3.11/dist-packages (from gitpython!=3.1.19,<4,>=3.0.7->streamlit) (4.0.12)\n",
            "Requirement already satisfied: six>=1.5 in /usr/local/lib/python3.11/dist-packages (from python-dateutil>=2.8.2->pandas) (1.17.0)\n",
            "Requirement already satisfied: charset-normalizer<4,>=2 in /usr/local/lib/python3.11/dist-packages (from requests<3,>=2.27->streamlit) (3.4.2)\n",
            "Requirement already satisfied: idna<4,>=2.5 in /usr/local/lib/python3.11/dist-packages (from requests<3,>=2.27->streamlit) (3.10)\n",
            "Requirement already satisfied: urllib3<3,>=1.21.1 in /usr/local/lib/python3.11/dist-packages (from requests<3,>=2.27->streamlit) (2.4.0)\n",
            "Requirement already satisfied: certifi>=2017.4.17 in /usr/local/lib/python3.11/dist-packages (from requests<3,>=2.27->streamlit) (2025.4.26)\n",
            "Requirement already satisfied: smmap<6,>=3.0.1 in /usr/local/lib/python3.11/dist-packages (from gitdb<5,>=4.0.1->gitpython!=3.1.19,<4,>=3.0.7->streamlit) (5.0.2)\n",
            "Requirement already satisfied: MarkupSafe>=2.0 in /usr/local/lib/python3.11/dist-packages (from jinja2->altair<6,>=4.0->streamlit) (3.0.2)\n",
            "Requirement already satisfied: attrs>=22.2.0 in /usr/local/lib/python3.11/dist-packages (from jsonschema>=3.0->altair<6,>=4.0->streamlit) (25.3.0)\n",
            "Requirement already satisfied: jsonschema-specifications>=2023.03.6 in /usr/local/lib/python3.11/dist-packages (from jsonschema>=3.0->altair<6,>=4.0->streamlit) (2025.4.1)\n",
            "Requirement already satisfied: referencing>=0.28.4 in /usr/local/lib/python3.11/dist-packages (from jsonschema>=3.0->altair<6,>=4.0->streamlit) (0.36.2)\n",
            "Requirement already satisfied: rpds-py>=0.7.1 in /usr/local/lib/python3.11/dist-packages (from jsonschema>=3.0->altair<6,>=4.0->streamlit) (0.25.1)\n",
            "Downloading streamlit-1.45.1-py3-none-any.whl (9.9 MB)\n",
            "\u001b[2K   \u001b[90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m \u001b[32m9.9/9.9 MB\u001b[0m \u001b[31m50.1 MB/s\u001b[0m eta \u001b[36m0:00:00\u001b[0m\n",
            "\u001b[?25hDownloading pydeck-0.9.1-py2.py3-none-any.whl (6.9 MB)\n",
            "\u001b[2K   \u001b[90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m \u001b[32m6.9/6.9 MB\u001b[0m \u001b[31m44.9 MB/s\u001b[0m eta \u001b[36m0:00:00\u001b[0m\n",
            "\u001b[?25hDownloading watchdog-6.0.0-py3-none-manylinux2014_x86_64.whl (79 kB)\n",
            "\u001b[2K   \u001b[90m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m \u001b[32m79.1/79.1 kB\u001b[0m \u001b[31m5.3 MB/s\u001b[0m eta \u001b[36m0:00:00\u001b[0m\n",
            "\u001b[?25hInstalling collected packages: watchdog, pydeck, streamlit\n",
            "Successfully installed pydeck-0.9.1 streamlit-1.45.1 watchdog-6.0.0\n"
          ]
        }
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "import streamlit as st\n",
        "import pandas as pd\n",
        "import plotly.express as px\n",
        "from datetime import datetime\n",
        "\n",
        "st.set_page_config(page_title=\"Dashboard de EPI\", layout=\"wide\")\n",
        "st.title(\"📊 Dashboard de Inspeção de EPI\")\n",
        "\n",
        "# Upload do arquivo\n",
        "uploaded_file = st.file_uploader(\"Faça upload do Excel com os dados\", type=[\"xlsx\"])\n",
        "\n",
        "if uploaded_file:\n",
        "    df = pd.read_excel(uploaded_file)\n",
        "\n",
        "    # Padronizar colunas\n",
        "    df.columns = [col.strip().replace(\" \", \"_\").replace(\".\", \"\").upper() for col in df.columns]\n",
        "\n",
        "    # Converter data\n",
        "    df['LINHAMAISRECENTEINSPECAO_DATA_INSPECAO'] = pd.to_datetime(\n",
        "        df['LINHAMAISRECENTEINSPECAO_DATA_INSPECAO'], errors='coerce'\n",
        "    )\n",
        "\n",
        "    # Última inspeção por técnico + EPI\n",
        "    df = df.sort_values(by='LINHAMAISRECENTEINSPECAO_DATA_INSPECAO', ascending=False)\n",
        "    df = df.drop_duplicates(subset=['TECNICO', 'PRODUTO_SIMILAR'], keep='first')\n",
        "\n",
        "    # Dias sem inspeção\n",
        "    df['DIAS_SEM_INSPECAO'] = (datetime.today() - df['LINHAMAISRECENTEINSPECAO_DATA_INSPECAO']).dt.days\n",
        "    df['PENDENTE'] = df['DIAS_SEM_INSPECAO'].isna() | (df['DIAS_SEM_INSPECAO'] > 180)\n",
        "\n",
        "    # Filtro de produto\n",
        "    epis = df['PRODUTO_SIMILAR'].dropna().unique()\n",
        "    tipo_selecionado = st.selectbox(\"Filtrar por Tipo de EPI:\", [\"TODOS\"] + sorted(epis.tolist()))\n",
        "\n",
        "    df_filtrado = df if tipo_selecionado == \"TODOS\" else df[df['PRODUTO_SIMILAR'] == tipo_selecionado]\n",
        "\n",
        "    # Gráfico 1 - Ranking por Coordenador\n",
        "    ranking_coord = df_filtrado.groupby('LINHAMAISRECENTEMICROSIGA_COORDENADOR_IMEDIATO')['PENDENTE'] \\\n",
        "        .value_counts().unstack().fillna(0)\n",
        "    if 'PENDENTE' not in ranking_coord.columns: ranking_coord['PENDENTE'] = 0\n",
        "    if 'OK' not in ranking_coord.columns: ranking_coord['OK'] = 0\n",
        "    ranking_coord['TOTAL'] = ranking_coord.sum(axis=1)\n",
        "    ranking_coord['% PENDENTE'] = (ranking_coord['PENDENTE'] / ranking_coord['TOTAL']) * 100\n",
        "\n",
        "    fig = px.bar(\n",
        "        ranking_coord.reset_index(),\n",
        "        x='LINHAMAISRECENTEMICROSIGA_COORDENADOR_IMEDIATO',\n",
        "        y='% PENDENTE',\n",
        "        title='📈 Ranking de Coordenadores - % de Técnicos com Pendência',\n",
        "        labels={'LINHAMAISRECENTEMICROSIGA_COORDENADOR_IMEDIATO': 'Coordenador'},\n",
        "        color='% PENDENTE',\n",
        "        color_continuous_scale='Reds'\n",
        "    )\n",
        "    fig.update_layout(xaxis_tickangle=-45)\n",
        "    st.plotly_chart(fig, use_container_width=True)\n",
        "\n",
        "    # Gráfico 2 - Por tipo de EPI (se for TODOS)\n",
        "    if tipo_selecionado == \"TODOS\":\n",
        "        resumo_epi = df.groupby('PRODUTO_SIMILAR')['PENDENTE'].value_counts().unstack().fillna(0)\n",
        "        resumo_epi['TOTAL'] = resumo_epi.sum(axis=1)\n",
        "        resumo_epi['% PENDENTE'] = (resumo_epi[True] / resumo_epi['TOTAL']) * 100\n",
        "\n",
        "        fig_epi = px.bar(\n",
        "            resumo_epi.reset_index(),\n",
        "            x='PRODUTO_SIMILAR',\n",
        "            y='% PENDENTE',\n",
        "            title='📌 Pendência por Tipo de EPI',\n",
        "            color='% PENDENTE',\n",
        "            color_continuous_scale='Blues'\n",
        "        )\n",
        "        fig_epi.update_layout(xaxis_tickangle=-45)\n",
        "        st.plotly_chart(fig_epi, use_container_width=True)\n",
        "\n",
        "    # Tabela de técnicos com pendência\n",
        "    st.subheader(\"🧾 Técnicos com Pendência\")\n",
        "    df_pend = df_filtrado[df_filtrado['PENDENTE'] == True]\n",
        "    st.dataframe(df_pend[[\n",
        "        'TECNICO', 'PRODUTO_SIMILAR', 'LINHAMAISRECENTEINSPECAO_DATA_INSPECAO',\n",
        "        'DIAS_SEM_INSPECAO', 'LINHAMAISRECENTEMICROSIGA_COORDENADOR_IMEDIATO',\n",
        "        'LINHAMAISRECENTEMICROSIGA_SUPERVISOR',\n",
        "        'LINHAMAISRECENTEMICROSIGA_GERENTE_IMEDIATO'\n",
        "    ]])\n"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "2m-ig6YIxq8V",
        "outputId": "4fee5e1f-04b9-4daa-a992-9c6bebbcea45"
      },
      "execution_count": 2,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stderr",
          "text": [
            "2025-05-29 16:01:41.242 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.244 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.390 \n",
            "  \u001b[33m\u001b[1mWarning:\u001b[0m to view this Streamlit app on a browser, run it with the following\n",
            "  command:\n",
            "\n",
            "    streamlit run /usr/local/lib/python3.11/dist-packages/colab_kernel_launcher.py [ARGUMENTS]\n",
            "2025-05-29 16:01:41.393 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.395 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.397 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.398 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.400 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n",
            "2025-05-29 16:01:41.402 Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.\n"
          ]
        }
      ]
    }
  ]
}