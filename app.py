import streamlit as st
import pandas as pd
import io

# Configuração da página
st.set_page_config(page_title="Tradutor de Tabelas Registro", layout="wide")
st.title("Automação de Limpeza e Tradução")
st.markdown("Suba seus arquivos CSV ou Excel (Xlsx) para aplicar o dicionário global.")

# 1. Upload dos Arquivos
with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        dic_file = st.file_uploader("Suba o arquivo de dicionário (CSV ou Excel)", type=['csv', 'xlsx'])

    with col2:
        fato_files = st.file_uploader("Suba as tabelas Registro (fato) (Pode selecionar várias)", type=['csv', 'xlsx'], accept_multiple_files=True)

# 2. Processamento
if dic_file and fato_files:
    
    if dic_file.name.endswith('.csv'):
        dic_df = pd.read_csv(dic_file, sep=None, engine='python')
    else:
        dic_df = pd.read_excel(dic_file)

    mapa_global = {}
    ignorar = ['antigo', 'novo', 'nan', 'dim_analista', 'dim_orgao', 'dim_cliente']
    
    for i in range(len(dic_df.columns) - 1):
        for a, n in zip(dic_df.iloc[:, i], dic_df.iloc[:, i+1]):
            if pd.notna(a) and pd.notna(n):
                a_s, n_s = str(a).strip(), str(n).strip()
                if a_s.lower() not in ignorar and not a_s.lower().startswith('unnamed'):
                    mapa_global[a_s] = n_s

    st.success(f"Dicionário carregado com {len(mapa_global)} termos mapeados!")
    st.divider()

    col_ajuda, col_resultado = st.columns([1, 2])

    with col_ajuda:
        st.info("[preencher]")

    with col_resultado:
        st.subheader("Processando Arquivos...")

        formato_saida = st.radio("Formato de saída", ["CSV", "Excel"], horizontal=True)

        colunas_alvo = ['dim_analista', 'dim_orgao', 'dim_identificacaoprojeto', 'dim_cliente']

        for file in fato_files:

            if file.name.endswith('.csv'):
                df = pd.read_csv(file, sep=None, engine='python')
            else:
                df = pd.read_excel(file)

            for col in colunas_alvo:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().replace(mapa_global)

            nome_base = file.name.rsplit('.', 1)[0]

            # ALTERAÇÃO 1: label do expander atualizado
            with st.expander(f"👁️ Visualizar Prévia tabela Processada: {file.name}"):
                st.dataframe(df.head(10))

            if formato_saida == "CSV":
                buffer = io.StringIO()
                df.to_csv(buffer, index=False, sep=';', encoding='utf-8-sig')
                st.download_button(
                    # ALTERAÇÃO 2: label do botão CSV atualizado
                    label=f"Clique aqui para baixar planilha processada: {nome_base}_processada",
                    data=buffer.getvalue(),
                    file_name=f"{nome_base}_processada.csv",
                    mime="text/csv",
                    key=f"download_{file.name}"
                )
            else:
                buffer = io.BytesIO()
                df.to_excel(buffer, index=False)
                st.download_button(
                    # ALTERAÇÃO 3: label do botão Excel atualizado
                    label=f"Clique aqui para baixar planilha processada: {nome_base}_processada",
                    data=buffer.getvalue(),
                    file_name=f"{nome_base}_processada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{file.name}"
                )

else:
    st.info("Aguardando o upload do dicionário e das tabelas fato para começar.")
