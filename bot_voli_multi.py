import os
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGINS = (os.getenv("ORIGINS") or "FCO").split(",")
DESTINATIONS = (os.getenv("DESTINATIONS") or "LHR").split(",")

DEPARTURE_DATE = os.getenv("DEPARTURE_DATE")
RETURN_DATE = os.getenv("RETURN_DATE")

ADULTS = int(os.getenv("ADULTS") or "2")
CURRENCY = os.getenv("CURRENCY") or "EUR"
MAX_PRICE = float(os.getenv("MAX_PRICE") or "250")

SERPAPI_URL = "https://serpapi.com/search.json"


def invia_notifica_telegram(messaggio):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Notifica Telegram non configurata.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": messaggio
        },
        timeout=30
    )

    if response.status_code == 200:
        print("Notifica Telegram inviata.")
    else:
        print("Errore invio notifica Telegram:")
        print(response.text)


def cerca_voli(origin, destination):
    params = {
        "engine": "google_flights",
        "api_key": SERPAPI_KEY,
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": DEPARTURE_DATE,
        "return_date": RETURN_DATE,
        "adults": ADULTS,
        "currency": CURRENCY,
        "hl": "it",
        "gl": "it",
        "type": "1"
    }

    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=60
    )

    if response.status_code != 200:
        print(f"\nErrore su {origin} → {destination}")
        print(f"HTTP {response.status_code}")
        print(response.text)
        return None

    return response.json()


def estrai_volo_piu_economico(dati):
    if not dati:
        return None

    voli = []

    voli.extend(dati.get("best_flights", []))
    voli.extend(dati.get("other_flights", []))

    voli_validi = [
        volo
        for volo in voli
        if isinstance(volo.get("price"), (int, float))
    ]

    if not voli_validi:
        return None

    return min(
        voli_validi,
        key=lambda volo: volo["price"]
    )


def crea_testo_volo(origin, destination, volo):
    prezzo = volo["price"]

    testo = (
        f"Volo trovato\n\n"
        f"Rotta: {origin} → {destination}\n"
        f"Prezzo totale per {ADULTS} persone: {prezzo} {CURRENCY}\n"
        f"Soglia impostata: {MAX_PRICE} {CURRENCY}\n"
    )

    for tratta in volo.get("flights", []):
        compagnia = tratta.get("airline", "N/D")
        partenza = tratta.get("departure_airport", {})
        arrivo = tratta.get("arrival_airport", {})

        testo += (
            f"\nCompagnia: {compagnia}\n"
            f"Partenza: {partenza.get('name', 'N/D')} - {partenza.get('time', 'N/D')}\n"
            f"Arrivo: {arrivo.get('name', 'N/D')} - {arrivo.get('time', 'N/D')}\n"
        )

    return testo


def stampa_risultato(origin, destination, volo):
    prezzo = volo["price"]

    print("\n" + "=" * 60)
    print(f"Rotta: {origin} → {destination}")
    print(f"Prezzo totale per {ADULTS} persone: {prezzo} {CURRENCY}")

    if prezzo <= MAX_PRICE:
        print("OFFERTA INTERESSANTE")
    else:
        print("Prezzo sopra la soglia")

    print("-" * 60)

    for tratta in volo.get("flights", []):
        compagnia = tratta.get("airline", "N/D")
        partenza = tratta.get("departure_airport", {})
        arrivo = tratta.get("arrival_airport", {})

        print(f"Compagnia: {compagnia}")
        print(f"Partenza: {partenza.get('name', 'N/D')} - {partenza.get('time', 'N/D')}")
        print(f"Arrivo: {arrivo.get('name', 'N/D')} - {arrivo.get('time', 'N/D')}")
        print()


def main():
    print("Avvio controllo prezzi voli")
    print(f"Partenza: {DEPARTURE_DATE}")
    print(f"Ritorno: {RETURN_DATE}")
    print(f"Adulti: {ADULTS}")
    print(f"Soglia prezzo: {MAX_PRICE} {CURRENCY}")

    if not SERPAPI_KEY:
        print("ERRORE: SERPAPI_KEY mancante")
        return

    for origin in ORIGINS:
        origin = origin.strip().upper()

        for destination in DESTINATIONS:
            destination = destination.strip().upper()

            print("\n" + "-" * 60)
            print(f"Controllo {origin} → {destination}")

            try:
                dati = cerca_voli(origin, destination)
                volo = estrai_volo_piu_economico(dati)

                if volo:
                    stampa_risultato(origin, destination, volo)

                    prezzo = volo["price"]

                    if prezzo <= MAX_PRICE:
                        messaggio = crea_testo_volo(origin, destination, volo)
                        invia_notifica_telegram(messaggio)
                else:
                    print("Nessun volo trovato.")

            except Exception as errore:
                print(f"Errore su {origin} → {destination}: {errore}")


if __name__ == "__main__":
    main()