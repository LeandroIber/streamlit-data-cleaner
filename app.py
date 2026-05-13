import csv
import io
import difflib

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================
COLUNAS_PRE_SELECIONADAS: list[str] = [
    'dim_analista',
    'dim_orgao',
    'dim_identificacaoprojeto',
    'dim_cliente',
]

# Tamanho da amostra usada para detectar o separador (8KB cobre dezenas de linhas)
_AMOSTRA_BYTES = 8192


# ============================================================
# LEITURA DE ARQUIVOS
# ============================================================

def _detectar_separador(amostra: str) -> str | None:
    
    #Tenta identificar o delimitador do CSV via csv.Sniffer.
    
    try:
        dialect = csv.Sniffer().sniff(amostra, delimiters=',;\t|')
        return dialect.delimiter
    except csv.Error:
        return None


def ler_arquivo(file, **kwargs) -> pd.DataFrame:
    """
    Lê CSV ou XLSX a partir do nome do arquivo.
     ValueError: se o arquivo não puder ser lido com nenhuma das estratégias.
    """
    nome = file.name.lower()

    # Excel: openpyxl cuida do encoding internamente
    if nome.endswith(('.xlsx', '.xls')):
        try:
            return pd.read_excel(file, **kwargs)
        except Exception as e:
            raise ValueError(f"Não foi possível ler o Excel: {e}") from e

    # CSV: tenta encodings em cascata
    for encoding in ('utf-8-sig', 'latin-1'):
        try:
            # 1. Espia uma amostra para descobrir o separador
            file.seek(0)
            amostra_bytes = file.read(_AMOSTRA_BYTES)
            amostra = (
                amostra_bytes.decode(encoding)
                if isinstance(amostra_bytes, bytes)
                else amostra_bytes
            )
            sep = _detectar_separador(amostra)

            # 2. Lê o arquivo todo: engine C se sabemos o sep, Python como fallback
            file.seek(0)
            if sep is not None:
                return pd.read_csv(
                    file, sep=sep, engine='c',
                    encoding=encoding, **kwargs
                )
            return pd.read_csv(
                file, sep=None, engine='python',
                encoding=encoding, **kwargs
            )

        except UnicodeDecodeError:
            # Encoding errado (pode falhar tanto no decode da amostra quanto no read_csv)
            continue
        except Exception as e:
            raise ValueError(f"Erro ao processar o CSV: {e}") from e

    raise ValueError(
        "Não foi possível decodificar o arquivo. "
        "Tente salvá-lo como UTF-8 ou converter para XLSX."
    )


def corrigir_semelhancas_automaticamente(serie_texto, grau_corte=0.85):
    """
    Identifica palavras muito parecidas e padroniza usando o termo mais frequente.
    """
    # Conta a frequência de cada termo (os mais frequentes ficam no topo)
    frequencias = serie_texto.value_counts()
    termos_unicos = frequencias.index.dropna().tolist()

    mapa_correcao = {}

    # Compara cada termo com os outros para achar os "quase iguais"
    for termo in termos_unicos:
        if termo in mapa_correcao:
            continue

        parecidos = difflib.get_close_matches(termo, termos_unicos, n=15, cutoff=grau_corte)

        for p in parecidos:
            mapa_correcao[p] = termo

    # Aplica a correção de uma vez só
    return serie_texto.replace(mapa_correcao)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(page_title="Datacleaner Automático", layout="wide")
st.title("Automação de Limpeza e Tradução")
st.markdown("Suba seus arquivos CSV ou XLSX para aplicar a Limpeza.")

# Inicializa a etapa
if 'etapa' not in st.session_state:
    st.session_state.etapa = 1


# --- TOPO SEMPRE VISÍVEL ---
col_upload, col_botao = st.columns([5, 1], vertical_alignment="bottom")

with col_upload:
    fato_files = st.file_uploader(
        "Upload das tabelas (Pode selecionar várias)",
        type=['csv', 'xlsx'],
        accept_multiple_files=True
    )

with col_botao:
    try:
        with open("Exemplo de tabela suja.csv", "rb") as file:
            st.download_button(
                label="Planilha Teste",
                data=file,
                file_name="Exemplo_de_tabela_suja.csv",
                mime="text/csv",
                # MUDANÇA AQUI: False faz o botão ficar no tamanho original do texto
                use_container_width=False,
                help="Baixe um exemplo para testar as funcionalidades agora mesmo."
            )
    except FileNotFoundError:
        st.error("Arquivo de exemplo não encontrado.")


# ============================================================
# CACHE DE DATAFRAMES
# ============================================================
# Streamlit re-executa o script inteiro a cada interação. Para não reler
# os arquivos do disco em toda etapa, carregamos uma vez só e guardamos
# os DataFrames no session_state. A chave (nome, tamanho) detecta se o
# usuário trocou os arquivos.

if fato_files:
    cache_key = tuple((f.name, f.size) for f in fato_files)
    if st.session_state.get('cache_key') != cache_key:
        with st.spinner("Carregando arquivos..."):
            dataframes: dict[str, pd.DataFrame] = {}
            erros: list[tuple[str, str]] = []
            for file in fato_files:
                file.seek(0)
                try:
                    dataframes[file.name] = ler_arquivo(file)
                except ValueError as e:
                    erros.append((file.name, str(e)))
            st.session_state.dataframes = dataframes
            st.session_state.erros_carregamento = erros
            st.session_state.cache_key = cache_key
            st.session_state.etapa = 1  # novos arquivos = volta para o início

    # Mostra erros de leitura uma vez, visível em qualquer etapa
    for nome, erro in st.session_state.get('erros_carregamento', []):
        st.error(f"Não conseguimos ler `{nome}`. Esse arquivo será ignorado.")
        st.caption(f"Detalhe técnico: {erro}")

    # Indicador visual de progresso
    etapa_labels = {1: "1. Escolher Colunas", 2: "2. Criar Dicionário", 3: "3. Processar e Baixar"}
    st.info(f"**Etapa atual:** {etapa_labels.get(st.session_state.etapa, '')}")
    st.divider()


# ============================================================
# BLOCOS DE ETAPAS
# ============================================================

if fato_files and st.session_state.dataframes:

    # ETAPA 1 —> Escolher Colunas
    if st.session_state.etapa == 1:
        st.subheader("Etapa 1: Escolha as Colunas para Tradução")

        # Pega o primeiro DataFrame válido (em cache)
        primeiro_nome = next(iter(st.session_state.dataframes))
        df_temp = st.session_state.dataframes[primeiro_nome]
        todas_colunas = df_temp.columns.tolist()

        # Prévia dos dados originais
        with st.expander(f"Visualizar dados originais — {primeiro_nome}"):
            mostrar_mais = st.checkbox(
                "Expandir amostra para 150 linhas",
                value=False,
                key="expandir_etapa1"
            )
            linhas = 150 if mostrar_mais else 10
            st.dataframe(df_temp.head(linhas), width='stretch')

        # Pré-seleciona colunas configuradas no topo, se existirem no arquivo
        selecao_default = [c for c in COLUNAS_PRE_SELECIONADAS if c in todas_colunas]

        colunas_selecionadas = st.multiselect(
            "Selecione as colunas que devem receber a Substituição:",
            options=todas_colunas,
            default=selecao_default,
            help="Apenas colunas de texto serão processadas. Numéricas/data são ignoradas automaticamente."
        )

        # --- NOVO BLOCO DE AUTO-LIMPEZA ---
        st.markdown("##### Opções de Auto-Limpeza rápidas")
        # MUDANÇA 1: Agora são 3 colunas
        col_clean1, col_clean2, col_clean3 = st.columns(3)

        with col_clean1:
            auto_title = st.checkbox("Maiúsculas/Minúsculas", value=True)
            st.caption("Padroniza o texto (ex: 'maria' -> 'Maria').")

        with col_clean2:
            auto_spaces = st.checkbox("Remover espaços extras", value=True)
            st.caption("Remove espaços duplos (ex: 'Cloud   Corp' -> 'Cloud Corp').")

        # MUDANÇA 2: O novo botão
        with col_clean3:
            auto_fuzzy = st.checkbox("Agrupar nomes parecidos", value=False)
            st.caption("Junta erros de digitação (ex: 'Fastdelivery' e 'Fast Delivery').")

        if st.button("Ir para criação de regras", type="primary", disabled=not colunas_selecionadas):
            st.session_state.colunas_selecionadas = colunas_selecionadas
            st.session_state.auto_title = auto_title
            st.session_state.auto_spaces = auto_spaces
            # MUDANÇA 3: Salvar a escolha na memória
            st.session_state.auto_fuzzy = auto_fuzzy
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
            "Use o botão **+** para adicionar mais linhas."
        )

        # --- CORREÇÃO: Aplicar auto-limpeza na visualização da prévia ---
        with st.expander("Visualizar dados pré-processados (com auto-limpeza)"):
            primeiro_nome = next(iter(st.session_state.dataframes))
            
            # Criamos uma cópia temporária para não alterar o cache original
            df_preview = st.session_state.dataframes[primeiro_nome].copy()

            colunas_escolhidas = st.session_state.colunas_selecionadas
            colunas_validas = [c for c in colunas_escolhidas if c in df_preview.columns]
            
            if colunas_validas:
                # Aplicamos as mesmas regras de limpeza da Etapa 3 na nossa prévia
                for col in colunas_validas:
                    eh_texto = (
                        pd.api.types.is_object_dtype(df_preview[col])
                        or pd.api.types.is_string_dtype(df_preview[col])
                    )
                    
                    if eh_texto:
                        mask = df_preview[col].notna()
                        # Padronização básica (strip)
                        serie = df_preview.loc[mask, col].astype(str).str.strip()
                        
                        # Espaços extras
                        if st.session_state.get('auto_spaces', False):
                            serie = serie.replace(r'\s+', ' ', regex=True)
                            
                        # Capitalização
                        if st.session_state.get('auto_title', False):
                            serie = serie.str.title()

                        # NOVO: Aplica o agrupamento inteligente na prévia
                        if st.session_state.get('auto_fuzzy', False):
                            serie = corrigir_semelhancas_automaticamente(serie)

                        df_preview.loc[mask, col] = serie

                mostrar_mais = st.checkbox(
                    "Expandir amostra para 150 linhas",
                    value=False,
                    key="expandir_etapa2"
                )
                linhas = 150 if mostrar_mais else 10
                st.dataframe(df_preview[colunas_validas].head(linhas), width='stretch')
            else:
                st.warning("Nenhuma das colunas selecionadas foi encontrada na prévia.")

        df_vazio = pd.DataFrame({"Antigo": [""], "Novo": [""]})

        dicionario_editado = st.data_editor(
            df_vazio,
            num_rows="dynamic",
            width='stretch',
            column_config={
                "Antigo": st.column_config.TextColumn("Termo Antigo (como aparece acima)"),
                "Novo":   st.column_config.TextColumn("Termo Novo (traduzido)"),
            }
        )
        # --- FIM DA CORREÇÃO ---

        # --- NOVO BLOCO DE LÓGICA DE ATIVAÇÃO ---
        col_voltar, col_avancar = st.columns([1, 3])

        with col_voltar:
            if st.button("Voltar"):
                st.session_state.etapa = 1
                st.rerun()

        with col_avancar:
            # 1. Identifica se há regras válidas no dicionário
            linhas_validas = dicionario_editado.dropna(subset=["Antigo", "Novo"])
            linhas_validas = linhas_validas[
                (linhas_validas["Antigo"].astype(str).str.strip() != "") &
                (linhas_validas["Novo"].astype(str).str.strip() != "")
            ]

            # 2. Verifica as condições (Regras OU Filtros de Auto-Limpeza)
            tem_regras = len(linhas_validas) > 0
            tem_autolimpeza = st.session_state.get('auto_title', False) or st.session_state.get('auto_spaces', False)

            # O botão fica desabilitado apenas se AMBOS forem falsos
            btn_disabled = not (tem_regras or tem_autolimpeza)

            if st.button("Aplicar Limpeza!", type="primary", disabled=btn_disabled):
                st.session_state.dicionario_editado = dicionario_editado
                st.session_state.etapa = 3
                st.rerun()

        # 3. Mensagens de feedback inteligentes
        if not tem_regras and not tem_autolimpeza:
            st.warning("Adicione uma regra ou ative uma Auto-Limpeza na Etapa 1 para continuar.")
        elif not tem_regras and tem_autolimpeza:
            st.info("Nenhuma regra de dicionário definida. Apenas a Auto-Limpeza será aplicada.")
        else:
            st.success(f"{len(linhas_validas)} regra(s) e filtros automáticos prontos.")

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

        for nome_arquivo, df_original in st.session_state.dataframes.items():
            # IMPORTANTE: copia antes de modificar — o original fica intocado no
            # cache, permitindo que o usuário volte e refaça com outro dicionário.
            df = df_original.copy()
            colunas_ignoradas: list[tuple[str, str]] = []  # (nome, dtype)

            for col in colunas_alvo:
                if col not in df.columns:
                    continue

                # Substituição de dicionário só se aplica a colunas de texto.
                # No pandas 3.0+ atribuir string em coluna numérica via .loc
                # levanta TypeError, então pulamos explicitamente.
                eh_texto = (
                    pd.api.types.is_object_dtype(df[col])
                    or pd.api.types.is_string_dtype(df[col])
                )
                if not eh_texto:
                    colunas_ignoradas.append((col, str(df[col].dtype)))
                    continue

                # --- NOVO BLOCO DE PROCESSAMENTO DE AUTO-LIMPEZA ---
                # Isola apenas os dados válidos (ignorando NaN reais)
                mask_nao_nulo = df[col].notna()
                
                # Passo A: Converte para string e limpa pontas (padrão)
                serie_texto = df.loc[mask_nao_nulo, col].astype(str).str.strip()

                # Passo B: Auto-Limpeza de Espaços (Regex)
                if st.session_state.get('auto_spaces', False):
                    serie_texto = serie_texto.replace(r'\s+', ' ', regex=True)

                # Passo C: Auto-Limpeza de Capitalização (Title Case)
                if st.session_state.get('auto_title', False):
                    serie_texto = serie_texto.str.title()

                # NOVO: Passo C.2: Inteligência de Agrupamento (Fuzzy Matching)
                if st.session_state.get('auto_fuzzy', False):
                    serie_texto = corrigir_semelhancas_automaticamente(serie_texto)

                # Passo D: Aplica o Dicionário customizado do usuário
                if mapa_global:
                    serie_texto = serie_texto.replace(mapa_global)

                # Devolve os dados limpos para a coluna original do DataFrame
                df.loc[mask_nao_nulo, col] = serie_texto

            # Avisa, uma vez por arquivo, as colunas que foram puladas
            if colunas_ignoradas:
                detalhes = ', '.join(f"`{c}` ({t})" for c, t in colunas_ignoradas)
                st.warning(
                    f"Em `{nome_arquivo}`, as colunas {detalhes} foram ignoradas "
                    "porque não são de texto (substituição via dicionário só se aplica a strings)."
                )

            with st.expander(f"Visualizar: {nome_arquivo}"):
                mostrar_mais = st.checkbox(
                    "Expandir amostra para 150 linhas",
                    value=False,
                    key=f"expandir_etapa3_{nome_arquivo}"
                )
                linhas = 150 if mostrar_mais else 10
                st.dataframe(df.head(linhas), width='stretch')

            # Nome base sem extensão
            nome_base = nome_arquivo.rsplit('.', 1)[0]

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
                    label=f"Download {nome_arquivo} como CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{nome_base}_processada.csv",
                    mime="text/csv",
                    key=f"csv_{nome_arquivo}"
                )
            with col_xlsx:
                st.download_button(
                    label=f"Download {nome_arquivo} como XLSX",
                    data=xlsx_buffer.getvalue(),
                    file_name=f"{nome_base}_processada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xlsx_{nome_arquivo}"
                )

        st.divider()
        if st.button("Voltar"):
            st.session_state.etapa = 1
            if 'colunas_selecionadas' in st.session_state:
                del st.session_state.colunas_selecionadas
            if 'dicionario_editado' in st.session_state:
                del st.session_state.dicionario_editado
            st.rerun()

elif fato_files and not st.session_state.dataframes:
    # Caso extremo: todos os arquivos enviados falharam na leitura
    st.warning("Nenhum dos arquivos enviados pôde ser lido. Verifique os erros acima e tente novamente.")

else:
    st.info("Aguardando o upload das tabelas fato para começar.")
