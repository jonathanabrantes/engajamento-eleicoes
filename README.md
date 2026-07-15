# Engajamento Eleições

Bot + dashboard para histórico de seguidores no Instagram dos pré-candidatos:

- Renan Santos (`@renansantosmbl`)
- Flávio Bolsonaro (`@flaviobolsonaro`)
- Lula (`@lulaoficial`)
- Caiado (`@ronaldocaiado`)
- Zema (`@romeuzemaoficial`)

O gráfico principal (estilo linha com rótulos nos pontos) destaca **Renan, Flávio e Lula**. Os cinco entram nos cards e no CSV.

## Como funciona

1. `bot/fetch.py` abre cada perfil no Chromium/Selenium (com cookie; sem API)
2. Grava contagens em `data/followers.csv`
3. Salva o **HTML** de cada perfil e compacta em `data/evidence/YYYYMMDDTHHMMSSZ.zip`
4. `cron.sh` roda **hora a hora**, faz commit (CSV + zip) e `git push`
5. GitHub Actions publica o front no **GitHub Pages**

O zip contém `{username}.html` de cada perfil + `meta.json` (seguidores, delta, url).

## Setup neste PC

```bash
./setup.sh
# cookie do Instagram em .cookies (header Cookie) — obrigatório
./cron.sh   # coleta manual
```

Cron instalado: `5 * * * *` (minuto 5 de cada hora).
