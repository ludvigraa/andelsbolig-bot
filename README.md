# Andelsbolig-bot (København)

Overvåger åbne boligportaler for **nye andelsbolig-opslag i København** og sender
en **Telegram-notifikation** (telefon + computer) så snart et nyt opslag dukker op —
med titel, pris, område og direkte link, så du kan reagere først.

Kilder i v1 (server-renderede, ingen login/Cloudflare):

- [andelsboliger.dk](https://www.andelsboliger.dk/andelsboliger/koebenhavn) — Danmarks største andelsbolig-portal
- [boligdeal.dk](https://www.boligdeal.dk/andelsboliger/koebenhavn) — aggregator

> **Forventning:** botten kører gratis via GitHub Actions hvert ~5. minut. Under load
> kan Actions forsinke kørsler, så notifikation kommer typisk **5–15 min** efter et
> opslag — ikke i sekundet. Vil du have ~30–60 sek, kør den på en lille VPS i stedet
> (samme kode, se nederst).

## Arkitektur

```
scraper/
  sources/        # én fil pr. portal (pluggable)
    base.py       # Listing-dataclass + Source-interface + HTTP-helper
    _itemcard.py  # fælles parser for "item-card"-portaler
    andelsboliger_dk.py
    boligdeal.py
  notify.py       # Telegram-afsender
  state.py        # husker sete opslag (state/seen.json)
  main.py         # hent → find nye → notificér → gem
```

Nye portaler tilføjes ved at lægge en fil i `scraper/sources/` (arv fra `Source`,
returnér `list[Listing]`) og registrere den i `build_sources()` i `main.py`.

## Opsætning

### 1. Lav en Telegram-bot
1. Skriv til **@BotFather** i Telegram → `/newbot` → følg trinene → kopiér **token**.
2. Skriv mindst én besked til din nye bot (ellers kan den ikke skrive til dig).
3. Find din **chat-id**: skriv til **@userinfobot**, eller åbn
   `https://api.telegram.org/bot<DIT_TOKEN>/getUpdates` i en browser og find
   `"chat":{"id":...}`.

### 2. Lokal test
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # udfyld TELEGRAM_BOT_TOKEN og TELEGRAM_CHAT_ID

python -m scraper.notify --test     # forventet: testbesked i Telegram
python -m scraper.main --dry-run    # forventet: liste af fundne opslag, intet sendt
python -m scraper.main              # første kørsel: "bot er live", markerer alt set
```

### 3. Kør gratis 24/7 i skyen (GitHub Actions)
1. Push dette repo til GitHub.
2. **Settings → Secrets and variables → Actions → New repository secret**, opret:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. **Actions**-fanen → vælg *Tjek andelsboliger* → **Run workflow** (manuel testkørsel).
4. Derefter kører den automatisk hvert 5. minut. State gemmes i `state/seen.json`,
   som workflowet committer tilbage mellem kørsler.

## Sådan undgås spam
Første kørsel markerer alle eksisterende opslag som "set" og sender kun én
*"bot er live"*-besked. Derefter notificeres kun **nye** opslag (ny dedup-nøgle
`kilde:id`). Fjernede opslag huskes, så de ikke dukker op igen ved genopslag.

## Hurtigere end 5 min? (VPS)
Koden er runner-agnostisk. På en lille server kan du droppe Actions og i stedet køre
i et loop, fx:
```bash
while true; do python -m scraper.main; sleep 60; done
```
med `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` i miljøet.

## Mulige udvidelser
- Filtre: max-pris, antal værelser, bestemte bydele/postnumre.
- Flere portaler (mæglersites: Nybolig, EDC, Home).
- Boliga/Boligsiden kræver omgåelse af Cloudflare (browser/curl_cffi) — bevidst udeladt i v1.
```
