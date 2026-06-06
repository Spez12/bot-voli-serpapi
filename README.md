# Bot Voli Amadeus

Questo progetto controlla i prezzi dei voli tramite Amadeus API.

## File principali

- `bot_voli_multi.py`: programma Python principale.
- `requirements.txt`: librerie da installare.
- `.env.example`: esempio di configurazione locale.
- `.github/workflows/controllo-voli.yml`: workflow GitHub Actions per eseguire il controllo automaticamente.

## Uso in locale

1. Installa Python.
2. Crea un ambiente virtuale:

```bash
python -m venv venv
```

3. Attiva l'ambiente virtuale:

```bash
venv\Scripts\activate
```

4. Installa le dipendenze:

```bash
pip install -r requirements.txt
```

5. Copia `.env.example` e rinominalo in `.env`.

6. Inserisci nel file `.env` le tue chiavi Amadeus.

7. Avvia il programma:

```bash
python bot_voli_multi.py
```

## Uso con GitHub Actions

Non caricare il file `.env`.

Vai nella repository GitHub:

`Settings → Secrets and variables → Actions → New repository secret`

Aggiungi questi secret:

- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `ORIGINS`
- `DESTINATIONS`
- `DEPARTURE_DATE`
- `RETURN_DATE`
- `ADULTS`
- `CURRENCY`
- `MAX_PRICE`

Poi vai su:

`Actions → Controllo Prezzi Voli → Run workflow`

## Esempio valori secret

```text
ORIGINS=PEG,FCO,PSA,BLQ
DESTINATIONS=LON,PAR,MAD,AMS
DEPARTURE_DATE=2026-08-10
RETURN_DATE=2026-08-15
ADULTS=2
CURRENCY=EUR
MAX_PRICE=250
```

## Nota

Il prezzo restituito è informativo. Prima di acquistare, controlla sempre il prezzo finale sul sito della compagnia o dell'agenzia.
