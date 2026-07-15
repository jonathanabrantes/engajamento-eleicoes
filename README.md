# Engajamento Eleições

Bot + dashboard para histórico de seguidores no Instagram dos pré-candidatos:

- Renan Santos (`@renansantosmbl`)
- Flávio Bolsonaro (`@flaviobolsonaro`)
- Lula (`@lulaoficial`)
- Caiado (`@ronaldocaiado`)
- Zema (`@romeuzemaoficial`)

O gráfico principal (estilo linha com rótulos nos pontos) destaca **Renan, Flávio e Lula**. Os cinco entram nos cards e no CSV.

## Como funciona

1. `bot/fetch.py` consulta os perfis via Chromium/Selenium
2. Grava em `data/followers.csv`
3. `cron.sh` roda **hora a hora**, faz commit e `git push`
4. GitHub Actions publica o front no **GitHub Pages**

## Setup neste PC

```bash
./setup.sh
# opcional: cookies do Instagram em .cookies (header Cookie)
./cron.sh   # primeira coleta manual
```

Cron instalado: `5 * * * *` (minuto 5 de cada hora).
