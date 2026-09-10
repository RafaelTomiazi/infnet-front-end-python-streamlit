# Desenvolvimento Front-End com Python (Streamlit) - Infnet

Rafael Celestino Tomiazi

Este repositorio guarda os testes de performance da disciplina de Front-End com
Python (Streamlit) do Infnet. Cada TP tem o seu proprio arquivo.

## TP2 - Dashboard COVID-19

Arquivo: `app.py`

Dashboard com 12 visualizacoes dos dados de COVID-19 no Brasil, usando os dados
do painel Coronavirus Brasil (https://covid.saude.gov.br/). Os arquivos CSV ficam
na pasta `dados`.

Rodar:

```
pip install streamlit pandas matplotlib seaborn altair plotly pydeck
streamlit run app.py
```

## TP3 - Turismo Data.Rio

Arquivo: `app_tp3_rafael_tomiazi.py`

Dashboard de turismo usando a tabela 3665 do portal Data.Rio (numero de visitantes
do Parque Nacional da Tijuca, por setor e por mes, com uma aba para cada ano). O
app faz a limpeza do arquivo na hora do upload, porque ele vem com linhas de titulo,
celulas mescladas e valores faltando.

Rodar:

```
pip install streamlit pandas plotly openpyxl
streamlit run app_tp3_rafael_tomiazi.py
```

Ao abrir, faca o upload do arquivo XLSX baixado do Data.Rio (tabela 3665).
