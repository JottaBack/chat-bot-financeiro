# Bot Financeiro

Projeto simples para registrar entradas e despesas e consultar resumos financeiros.

## Arquivos

- `bot_financeiro.py`: versao inicial do bot no terminal, sem persistencia dos dados.
- `meu_bot_financeiro/bot_financeiro_v2.py`: versao de terminal com dados armazenados em SQLite.
- `meu_bot_financeiro/painel.py`: painel web feito com Streamlit.

Os bancos SQLite (`*.db`) e os relatorios CSV gerados localmente estao ignorados pelo Git para nao publicar dados financeiros pessoais.

## Requisitos

Python 3.10 ou superior.

Instale as dependencias do painel:

```powershell
python -m pip install -r requirements.txt
```

## Como executar

Bot no terminal:

```powershell
python bot_financeiro.py
```

Versao de terminal com banco de dados:

```powershell
python meu_bot_financeiro/bot_financeiro_v2.py
```

O banco `meu_bot_financeiro/financeiro.db` e criado localmente quando essa versao e iniciada.

Painel web:

```powershell
streamlit run meu_bot_financeiro/painel.py
```

O painel usa o banco `meu_bot_financeiro/financeiro.db`. Se ele ainda nao existir, execute a versao de terminal com banco de dados uma vez para cria-lo.
