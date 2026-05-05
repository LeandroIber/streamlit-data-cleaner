import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Tradutor de Tabelas Registro", layout="wide")
st.title("Automação de Limpeza e Tradução")
st.markdown("Suba seus arquivos CSV para aplicar o dicionário global.")

# 1. Upload dos Arquivos
col1, col2 = st.columns(2)

with col1:
    # ALTERAÇÃO 1 adicionar opção xlsx: type agora aceita 'xlsx' além de 'csv' 
    dic_file = st.file_uploader("Suba o arquivo de dicionário (CSV ou Excel)", type=['csv', 'xlsx'])

with col2:
    # ALTERAÇÃO 2 adicionar opção xlsx: type agora aceita 'xlsx' além de 'csv' 
    fato_files = st.file_uploader("Suba as tabelas Registro (fato) (Pode selecionar várias)", type=['csv', 'xlsx'], accept_multiple_files=True)

# 2. Processamento
if dic_file and fato_files:

    # ALTERAÇÃO 3: leitura flexível do dicionário CSV ou XLSX
    if dic_file.name.endswith('.csv'):
        dic_df = pd.read_csv(dic_file, sep=None, engine='python')
    else:
        dic_df = pd.read_excel(dic_file)

    mapa_global = {}
    ignorar = ['antigo', 'novo', 'nan', 'dim_analista', 'dim_orgao', 'dim_cliente']
    
    # Criar o mapa de tradução
    for i in range(len(dic_df.columns) - 1):
        for a, n in zip(dic_df.iloc[:, i], dic_df.iloc[:, i+1]):
            if pd.notna(a) and pd.notna(n):
                a_s, n_s = str(a).strip(), str(n).strip()
                if a_s.lower() not in ignorar and not a_s.lower().startswith('unnamed'):
                    mapa_global[a_s] = n_s

    st.success(f"Dicionário carregado com {len(mapa_global)} termos mapeados!")

    st.divider()
    st.subheader("Processando Arquivos...")

    colunas_alvo = ['dim_analista', 'dim_orgao', 'dim_identificacaoprojeto', 'dim_cliente']

    for file in fato_files:

        # ALTERAÇÃO 4: leitura flexível das tabelas fato (registro)  CSV ou XLSX
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
        
        # Aplicar substituição
        for col in colunas_alvo:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace(mapa_global)
        
        # Mostrar prévia
        with st.expander(f"Visualizar: {file.name}"):
            st.dataframe(df.head(10))
        
        # Botão de Download para cada arquivo
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')
        
        st.download_button(
            label=f"📥 Baixar {file.name} Processado",
            data=csv_buffer.getvalue(),
            file_name=file.name.replace(".csv", "_processada.csv"),
            mime="text/csv"
        )

else:
    st.info("Aguardando o upload do dicionário e das tabelas fato para começar.")
