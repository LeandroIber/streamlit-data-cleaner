# Datacleaner with Pandas, Streamlit & Openpyxl

Aplicação web construída com Streamlit para automação de limpeza, padronização e tradução de tabelas de registro. A ferramenta permite a aplicação de regras customizáveis de substituição de dados ("De/Para") através de uma interface web.

Acesse a aplicação: [Datacleaner App](https://app-data-cleaner-ejwhjeasdmmplvmxzcsh2t.streamlit.app/)

## O Problema que este projeto resolve

Na área de dados, é comum lidar com planilhas contendo nomenclaturas fora do padrão, erros de digitação ou termos legados. Este aplicativo elimina a necessidade de executar substituições manuais no Excel ou de escrever scripts repetitivos para novas demandas de limpeza. Ele permite que o usuário selecione colunas específicas, crie regras de padronização na própria interface e aplique as correções em lote.

## Funcionalidades

O fluxo de uso da aplicação é dividido em três etapas:

- **1. Seleção de Colunas:** Upload de arquivos e definição de quais colunas receberão as modificações, incluindo uma pré-visualização dos dados originais.
- **2. Mapeamento de Dicionário:** Interface de grade editável para mapeamento dos termos "Antigos" e "Novos" em tempo de execução, dispensando o upload de um arquivo de dicionário externo.
- **3. Processamento em Lote:** Execução das substituições em múltiplas tabelas (CSV ou XLSX) simultaneamente. As transformações ocorrem em memória para reduzir operações de I/O em disco.
- **Exportação:** Geração dos arquivos processados para download direto nos formatos .csv e .xlsx.

## Tecnologias Utilizadas

- **Python:** Linguagem base do projeto.
- **Streamlit:** Framework utilizado para a construção da interface, navegação entre as etapas e gestão de estado (session_state).
- **Pandas:** Motor principal para leitura estruturada, manipulação dos DataFrames e aplicação das regras de substituição de texto.
- **Openpyxl:** Biblioteca para suporte a leitura e escrita de arquivos Excel (.xlsx).
