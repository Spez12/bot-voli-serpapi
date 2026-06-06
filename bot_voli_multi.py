import os
import urllib.parse
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGINS = [x.strip() for x in (os.getenv("ORIGINS") or "FCO").split(",")]
DESTINATIONS = [x.strip() for x in (os.getenv("DESTINATIONS") or "LHR").split(",")]

DEPARTURE_DATE = (os.getenv("DEPARTURE_DATE") or "").strip()
RETURN_DATE = (os.getenv("RETURN_DATE") or "").strip()

ADULTS = int((os.getenv("ADULTS") or "2").strip())
CURRENCY = (os.getenv("CURRENCY") or "EUR").strip()
MAX_PRICE = float((os.getenv("MAX_PRICE") or "250").strip())

SERPAPI_URL = "https://serpapi.com/search.json"


def crea_link_google_flights(origin, destination):
    testo = f"{origin} to {destination} {DEPARTURE_DATE} {RETURN_DATE}"
    query = urllib.parse.quote(testo)
    return f"https://www.google.com/travel/flights?q={query}"


def invia_notifica_telegram(messaggio):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Notifica Telegram non configurata.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": messaggio,
            "disable_web_page_preview": False
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

    response = requests.get(SERPAPI_URL, params=params, timeout=60)

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
        volo for volo in voli
        if isinstance(volo.get("price"), (int, float))
    ]

    if not voli_validi:
        return None

    return min(voli_validi, key=lambda volo: volo["price"])


def conta_scali(volo):
    tratte = volo.get("flights", [])
    return max(len(tratte) - 1, 0)


def crea_testo_volo(origin, destination, volo):
    prezzo = volo["price"]
    scali = conta_scali(volo)
    link = crea_link_google_flights(origin, destination)

    testo = (
        f"Volo trovato sotto soglia\n\n"
        f"Rotta: {origin} → {destination}\n"
        f"Prezzo totale per {ADULTS} persone: {prezzo} {CURRENCY}\n"
        f"Soglia impostata: {MAX_PRICE} {CURRENCY}\n"
        f"Scali: {scali}\n\n"
    )

    for tratta in volo.get("flights", []):
        compagnia = tratta.get("airline", "N/D")
        partenza = tratta.get("departure_airport", {})
        arrivo = tratta.get("arrival_airport", {})

        testo += (
            f"Compagnia: {compagnia}\n"
            f"Partenza: {partenza.get('name', 'N/D')} - {partenza.get('time', 'N/D')}\n"
            f"Arrivo: {arrivo.get('name', 'N/D')} - {arrivo.get('time', 'N/D')}\n\n"
        )

    testo += f"Apri ricerca Google Flights:\n{link}"

    return testo


def stampa_risultato(origin, destination, volo):
    prezzo = volo["price"]
    scali = conta_scali(volo)

    print("\n" + "=" * 60)
    print(f"Rotta: {origin} → {destination}")
    print(f"Prezzo totale per {ADULTS} persone: {prezzo} {CURRENCY}")
    print(f"Scali: {scali}")

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
        print(
            f"Partenza: {partenza.get('name', 'N/D')} "
            f"- {partenza.get('time', 'N/D')}"
        )
        print(
            f"Arrivo: {arrivo.get('name', 'N/D')} "
            f"- {arrivo.get('time', 'N/D')}"
        )
        print()


def main():
    print("DEBUG VARIABILI")
    print("SERPAPI_KEY presente =", bool(SERPAPI_KEY))
    print("TELEGRAM_BOT_TOKEN presente =", bool(TELEGRAM_BOT_TOKEN))
    print("TELEGRAM_CHAT_ID presente =", bool(TELEGRAM_CHAT_ID))
    print("ORIGINS =", repr(ORIGINS))
    print("DESTINATIONS =", repr(DESTINATIONS))
    print("DEPARTURE_DATE =", repr(DEPARTURE_DATE))
    print("RETURN_DATE =", repr(RETURN_DATE))
    print("ADULTS =", repr(ADULTS))
    print("CURRENCY =", repr(CURRENCY))
    print("MAX_PRICE =", repr(MAX_PRICE))

    print("\nAvvio controllo prezzi voli")
    print(f"Partenza: {DEPARTURE_DATE}")
    print(f"Ritorno: {RETURN_DATE}")
    print(f"Adulti: {ADULTS}")
    print(f"Soglia prezzo: {MAX_PRICE} {CURRENCY}")

    if not SERPAPI_KEY:
        print("ERRORE: SERPAPI_KEY mancante")
        return

    for origin in ORIGINS:
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
                        messaggio = crea_testo_volo(
                            origin,
                            destination,
                            volo
                        )

                        invia_notifica_telegram(
                            messaggio
                        )
                else:
                    print("Nessun volo trovato.")

            except Exception as errore:
                print(
                    f"Errore su {origin} → "
                    f"{destination}: {errore}"
                )


if __name__ == "__main__":
    main()
