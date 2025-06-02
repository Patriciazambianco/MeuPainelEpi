@st.cache
def carregar_dados():
    df = pd.read_excel("LISTA DE VERIFICAÇÃO EPI.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip()

    col_tec = [col for col in df.columns if 'TECNICO' in col.upper()]
    col_prod = [col for col in df.columns if 'PRODUTO' in col.upper()]
    col_data = [col for col in df.columns if 'INSPECAO' in col.upper()]

    if not col_tec or not col_prod or not col_data:
        st.error("❌ Verifique se o arquivo contém colunas de TÉCNICO, PRODUTO e INSPEÇÃO.")
        return pd.DataFrame()

    tecnico_col = col_tec[0]
    produto_col = col_prod[0]
    data_col = col_data[0]

    df.rename(columns={
        'GERENTE': 'GERENTE_IMEDIATO',
        'SITUAÇÃO CHECK LIST': 'STATUS CHECK LIST'
    }, inplace=True)

    df['Data_Inspecao'] = pd.to_datetime(df[data_col], errors='coerce')

    # Cria uma chave única TECNICO + PRODUTO
    df['CHAVE'] = df[tecnico_col].astype(str).str.strip() + "|" + df[produto_col].astype(str).str.strip()

    # Separar com e sem data
    df_com_data = df.dropna(subset=['Data_Inspecao']).copy()
    df_sem_data = df[df['Data_Inspecao'].isna()].copy()

    # Pegar a última inspeção por chave (técnico + produto)
    df_com_data.sort_values('Data_Inspecao', ascending=False, inplace=True)
    df_ultimos = df_com_data.drop_duplicates(subset='CHAVE', keep='first')

    # Filtrar pendentes SEM inspeção (sem estar entre os últimos)
    chaves_com_data = set(df_ultimos['CHAVE'])
    df_sem_data = df_sem_data[~df_sem_data['CHAVE'].isin(chaves_com_data)]

    # Junta os dois (última inspeção + pendentes nunca inspecionados)
    df_resultado = pd.concat([df_ultimos, df_sem_data], ignore_index=True)

    # Renomeia para padronizar
    df_resultado.rename(columns={
        tecnico_col: 'TECNICO',
        produto_col: 'PRODUTO'
    }, inplace=True)

    # Ajusta status e vencimento
    if 'STATUS CHECK LIST' in df_resultado.columns:
        df_resultado['STATUS CHECK LIST'] = df_resultado['STATUS CHECK LIST'].str.upper()

    hoje = pd.Timestamp.now().normalize()
    df_resultado['Dias_Sem_Inspecao'] = (hoje - df_resultado['Data_Inspecao']).dt.days
    df_resultado['Vencido'] = df_resultado['Dias_Sem_Inspecao'] > 180

    return df_resultado.drop(columns=['CHAVE'])
