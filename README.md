# Streamlit Data Cleaner

Aplicação Streamlit para automação de limpeza, padronização e tradução de tabelas de registro (tabelas fato) utilizando dicionários customizáveis.

## O Problema que este projeto resolve
Na área de dados, é comum receber planilhas com nomenclaturas fora do padrão. Este aplicativo elimina a necessidade de fazer substituições manuais ou usar scripts complexos repetitivos. Ele recebe um arquivo de dicionário com regras "De/Para" e aplica essa padronização em múltiplos arquivos CSV de forma automatizada e visual.

## Funcionalidades
- **Upload de Dicionário:** Carregue um arquivo CSV contendo as colunas com os termos antigos e novos.
- **Processamento em Lote (Batch):** Suba várias tabelas de registro (fato) ao mesmo tempo para processamento simultâneo.
- **Limpeza Inteligente:** O mecanismo de mapeamento global ignora metadados e valores nulos automaticamente para evitar distorções nos dados.
- **Download Simplificado:** Gere e baixe os novos arquivos CSV limpos e prontos para bancos de dados ou dashboards com um clique.

## Tecnologias Utilizadas
- Python: Linguagem base do projeto.
- Streamlit: Framework utilizado para a construção da interface web, upload de arquivos e botões de download.
- Pandas: Utilizado para a leitura dos CSVs, manipulação dos DataFrames e aplicação do dicionário de dados.

