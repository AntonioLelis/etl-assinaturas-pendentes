# Painel ETL: Assinaturas Pendentes

Este projeto é um dashboard interativo desenvolvido para automatizar o processo de ETL (Extração, Transformação e Carga) de relatórios de assinaturas pendentes dos profissionais da Secretaria Municipal de Saúde (SEMUS). Ele recebe arquivos CSV desestruturados exportados do sistema, normaliza os dados e fornece uma interface limpa para filtragem e análise gerencial.

## Funcionalidades

- **Limpeza Automática (Unpivoting):** Transforma relatórios gerados em formato de impressão em uma base de dados tabular limpa, extraindo CPFs ocultos e propagando IDs e vínculos corretamente.
- **Análise de Lotações:** Separa e identifica as múltiplas unidades (US, PA) em que um mesmo profissional atua, com uma trava de segurança analítica para não duplicar a soma total de documentos pendentes.
- **Filtros Dinâmicos:** Filtragem instantânea por Unidade de Saúde e Tipo de Vínculo (com tratamento automático para identificar profissionais "Externos").
- **Visualização de Dados:** Gráfico interativo destacando os maiores gargalos de assinaturas por unidade de saúde.
- **Exportação Flexível:** Download imediato dos dados tratados em formato `.csv` ou planilha `.xlsx` nativa.

## Tecnologias Utilizadas

- **Python**
- **Streamlit:** Construção da interface web interativa.
- **Pandas:** Limpeza, transformação e estruturação pesada dos dados.
- **Altair:** Renderização de gráficos otimizados e responsivos.
- **Openpyxl:** Motor de exportação para planilhas Excel estruturadas.

## Como executar localmente

1. Clone este repositório para a sua máquina:
   ```bash
   git clone (https://github.com/AntonioLelis/etl-assinaturas-pendentes.git)
   ```

2. Entre na pasta do projeto:
   ```bash
   cd assinaturas_pendentes
   ```

3. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute o painel do Streamlit:
   ```bash
   streamlit run app.py
   ```

## Deploy

Este projeto está configurado para deploy contínuo via **Streamlit Cloud**. Basta conectar a branch principal (`main`) na plataforma do Streamlit, e a aplicação fará a leitura automática do `requirements.txt` para provisionar o ambiente.

> **Nota de Privacidade:** O arquivo `.gitignore` está configurado para bloquear o upload de arquivos `.csv` e `.xlsx`, garantindo que nenhum dado real ou sensível de profissionais seja exposto no repositório público.