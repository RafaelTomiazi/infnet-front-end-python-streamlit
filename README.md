# TP2 - COVID-19 no Brasil

Dashboard feito em Python e Streamlit para explorar os dados do painel Coronavirus Brasil:
https://covid.saude.gov.br/

O arquivo `app.py` reúne os 12 exercícios da atividade. 
Deixei cada exercício marcado no código e
as respostas aparecem no próprio dashboard, junto dos gráficos.

## Como executar

1. Coloque os arquivos CSV do painel dentro da pasta `dados`.
2. Instale as bibliotecas:

```bash
pip install streamlit pandas matplotlib seaborn altair plotly pydeck
```

3. Inicie o dashboard:

```bash
streamlit run app.py
```

Para os mapas, o programa consulta uma base pública com latitude e longitude dos municípios.
