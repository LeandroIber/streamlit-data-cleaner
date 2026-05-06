import streamlit as st
import pandas as pd
import io


# --- Função auxiliar para leitura de CSV ou XLSX ---
def ler_arquivo(file, **kwargs):
    """Lê CSV ou XLSX a partir do nome do arquivo."""
    nome = file.name.lower()
    if nome.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file, **kwargs)
    return pd.read_csv(file, sep=None, engine='python', **kwargs)


# Configuração da página
st.set_page_config(page_title="Tradutor de Tabelas Registro", layout="wide")
st.title("Automação de Limpeza e Tradução")
st.markdown("Suba seus arquivos CSV ou XLSX para aplicar a substituição.")

# Passo 1: Inicializar a "memória" da etapa
if 'etapa' not in st.session_state:
    st.session_state.etapa = 1

# --- TOPO SEMPRE VISÍVEL ---
fato_files = st.file_uploader(
    "Upload das tabelas (Pode selecionar várias)",
    type=['csv', 'xlsx'],
    accept_multiple_files=True
)

# Indicador visual de progresso
if fato_files:
    etapa_labels = {1: "① Escolher Colunas", 2: "② Criar Dicionário", 3: "③ Processar e Baixar"}
    st.info(f"**Etapa atual:** {etapa_labels.get(st.session_state.etapa, '')}")
    st.divider()

# --- BLOCOS DE ETAPAS ---
if fato_files:

    
    # ETAPA 1 —> Escolher Colunas
    
    if st.session_state.etapa == 1:
        st.subheader("Etapa 1: Escolha as Colunas para Tradução")

        # "Espiadinha": lê as 10 primeiras linhas do primeiro arquivo
        primeiro_arquivo = fato_files[0]
        df_temp = ler_arquivo(primeiro_arquivo, nrows=10)
        primeiro_arquivo.seek(0)  # Reseta o cursor para leituras futuras

        todas_colunas = df_temp.columns.tolist()

        # Prévia dos dados originais
        with st.expander("Visualizar dados originais (10 primeiras linhas)"):
            st.dataframe(df_temp, width='stretch')

        # Pré-seleciona colunas padrão se existirem no arquivo
        colunas_padrao = ['dim_analista', 'dim_orgao', 'dim_identificacaoprojeto', 'dim_cliente']
        selecao_default = [c for c in colunas_padrao if c in todas_colunas]

        colunas_selecionadas = st.multiselect(
            "Selecione as colunas que devem receber a Substituição:",
            options=todas_colunas,
            default=selecao_default
        )

        if st.button("Ir para criação de regras →", type="primary", disabled=not colunas_selecionadas):
            st.session_state.colunas_selecionadas = colunas_selecionadas
            st.session_state.etapa = 2
            st.rerun()

        if not colunas_selecionadas:
            st.warning("Selecione ao menos uma coluna para continuar.")

    # ETAPA 2 —> Criar o Dicionário Dinâmico
    elif st.session_state.etapa == 2:
        st.subheader("Etapa 2: Monte o Dicionário de Tradução")
        st.markdown(
            "Preencha a tabela abaixo com os termos **Antigos** (como estão no CSV) "
            "e os termos **Novos** (como devem ficar). "
            "Use o botão **＋** para adicionar mais linhas."
        )

        # Prévia dos dados originais para consulta
        try:
            with st.expander("Visualizar dados originais (10 primeiras linhas)"):
                arquivo_consulta = fato_files[0]
                arquivo_consulta.seek(0)  # Garante cursor no início
                df_consulta = ler_arquivo(arquivo_consulta, nrows=10)
                arquivo_consulta.seek(0)  # Rebobina após a leitura

                # Filtra apenas colunas que realmente existem no arquivo
                colunas_escolhidas = st.session_state.colunas_selecionadas
                colunas_validas = [c for c in colunas_escolhidas if c in df_consulta.columns]
                if colunas_validas:
                    st.dataframe(df_consulta[colunas_validas], width='stretch')
                else:
                    st.warning("Nenhuma das colunas selecionadas foi encontrada na prévia.")
        except Exception as e:
            st.warning(f"Não foi possível carregar a prévia: {e}")

        df_vazio = pd.DataFrame({"Antigo": [""], "Novo": [""]})

        dicionario_editado = st.data_editor(
            df_vazio,
            num_rows="dynamic",
            width='stretch',
            column_config={
                "Antigo": st.column_config.TextColumn("Termo Antigo (original)"),
                "Novo":   st.column_config.TextColumn("Termo Novo (traduzido)"),
            }
        )

        col_voltar, col_avancar = st.columns([1, 3])
        with col_voltar:
            if st.button("← Voltar"):
                st.session_state.etapa = 1
                st.rerun()
        with col_avancar:
            # Conta linhas válidas (ambas as colunas preenchidas)
            linhas_validas = dicionario_editado.dropna(subset=["Antigo", "Novo"])
            linhas_validas = linhas_validas[
                (linhas_validas["Antigo"].str.strip() != "") &
                (linhas_validas["Novo"].str.strip() != "")
            ]
            btn_disabled = len(linhas_validas) == 0

            if st.button("Aplicar Limpeza! →", type="primary", disabled=btn_disabled):
                st.session_state.dicionario_editado = dicionario_editado
                st.session_state.etapa = 3
                st.rerun()

        if len(linhas_validas) == 0:
            st.warning("Adicione ao menos uma regra de tradução (Antigo → Novo) para continuar.")
        else:
            st.success(f"{len(linhas_validas)} regra(s) definida(s).")

    # ETAPA 3 > Processar e Download

    elif st.session_state.etapa == 3:
        st.subheader("Etapa 3: Arquivos Processados")

        # Reconstruir mapa global a partir do dicionário salvo no session_state
        dicionario_df = st.session_state.dicionario_editado
        colunas_alvo  = st.session_state.colunas_selecionadas

        mapa_global = {}
        ignorar = ['antigo', 'novo']

        for _, row in dicionario_df.iterrows():
            a = row.get("Antigo", None)
            n = row.get("Novo",   None)
            if pd.notna(a) and pd.notna(n):
                a_s, n_s = str(a).strip(), str(n).strip()
                if a_s.lower() not in ignorar and a_s != "":
                    mapa_global[a_s] = n_s

        st.success(f"Dicionário com **{len(mapa_global)}** termo(s) mapeado(s) | Colunas alvo: `{', '.join(colunas_alvo)}`")

        for file in fato_files:
            file.seek(0)
            df = ler_arquivo(file)

            for col in colunas_alvo:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().replace(mapa_global)

            with st.expander(f"Visualizar: {file.name}"):
                st.dataframe(df.head(10))

            # Nome base sem extensão
            nome_base = file.name.rsplit('.', 1)[0]

            # Buffer CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig')

            # Buffer XLSX
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')

            # Botões de download lado a lado (CSV e XLSX sempre disponíveis)
            col_csv, col_xlsx = st.columns(2)
            with col_csv:
                st.download_button(
                    label=f"Download {file.name} como CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{nome_base}_processada.csv",
                    mime="text/csv",
                    key=f"csv_{file.name}"
                )
            with col_xlsx:
                st.download_button(
                    label=f"Download {file.name} como XLSX",
                    data=xlsx_buffer.getvalue(),
                    file_name=f"{nome_base}_processada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xlsx_{file.name}"
                )

        st.divider()
        if st.button("Voltar"):
            st.session_state.etapa = 1
            if 'colunas_selecionadas' in st.session_state:
                del st.session_state.colunas_selecionadas
            if 'dicionario_editado' in st.session_state:
                del st.session_state.dicionario_editado
            st.rerun()

else:
    st.info("Aguardando o upload das tabelas fato para começar.")
