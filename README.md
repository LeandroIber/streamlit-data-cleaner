# Datacleaner with Pandas, Streamlit & Openpyxl

Aplicação web interativa construída com Streamlit para automação de limpeza, padronização e tradução de tabelas de registro. A ferramenta permite a aplicação de regras customizáveis de substituição de dados ("De/Para") de forma visual e intuitiva.

Acesse a aplicação: [Datacleaner App](https://app-data-cleaner-ejwhjeasdmmplvmxzcsh2t.streamlit.app/)

## O Problema que este projeto resolve

Na área de dados, é comum receber planilhas com nomenclaturas fora do padrão, erros de digitação ou termos legados. Este aplicativo elimina a necessidade de fazer substituições manuais demoradas no Excel ou de escrever scripts complexos e repetitivos para cada nova demanda. Ele permite que o usuário selecione colunas específicas, crie regras de padronização diretamente na interface e aplique essas correções em múltiplos arquivos de forma automatizada.

## Funcionalidades

O aplicativo funciona como um assistente em 3 etapas simples:

- **1. Seleção Direcionada:** Upload de arquivos e escolha exata de quais colunas devem receber o tratamento, com pré-visualização instantânea dos dados originais.
- **2. Criação Dinâmica de Dicionário:** Interface de grade editável para inserir, na hora, as regras com os termos "Antigos" e "Novos", sem a necessidade de fazer upload de um dicionário separado.
- **3. Processamento em Lote (Batch):** Suba e processe múltiplas tabelas (CSV ou XLSX) simultaneamente. O mecanismo atualiza os dados em memória, otimizando a performance da aplicação.
- **Exportação Flexível:** Download imediato dos arquivos processados disponíveis em formatos .csv e .xlsx com um único clique.

## Tecnologias Utilizadas

- **Python:** Linguagem base do projeto.
- **Streamlit:** Framework utilizado para a construção de toda a interface web, navegação entre as etapas e gestão do estado da aplicação (session_state).
- **Pandas:** Motor principal para leitura estruturada, manipulação dos DataFrames em memória e aplicação das regras de substituição de texto.
- **Openpyxl:** Biblioteca integrada para suporte nativo a leitura e escrita de arquivos Excel (.xlsx), garantindo compatibilidade com planilhas de negócios.
- 
## Autor

Desenvolvido por Leandro Iber.
