import os
import json
import urllib.parse
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGINS = [x.strip() for x in (os.getenv("ORIGINS") or "FCO").split(",")]
DESTINATIONS = [x.strip() for x in (os.getenv("DESTINATIONS") or "LHR").split(",")]

DEPARTURE_DATE = (os.getenv("DEPARTURE_DATE") or "").strip()
RETURN_DATE = (os.getenv("RETURN_DATE") or "").strip()
TRIP_PERIODS_RAW = (os.getenv("TRIP_PERIODS") or "").strip()

ADULTS = int((os.getenv("ADULTS") or "2").strip())
CURRENCY = (os.getenv("CURRENCY") or "EUR").strip()
MAX_PRICE = float((os.getenv("MAX_PRICE") or "250").strip())

SERPAPI_URL = "https://serpapi.com/search.json"
SUBSCRIBERS_FILE = "subscribers.json"
OFFSET_FILE = "telegram_offset.txt"


def carica_iscritti():
    try:
        with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def salva_iscritti(iscritti):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as file:
        json.dump(iscritti, file, indent=2)


def leggi_offset():
    try:
        with open(OFFSET_FILE, "r", encoding="utf-8") as file:
            valore = file.read().strip()
            return int(valore or "0")
    except FileNotFoundError:
        return 0
    except ValueError:
        return 0


def salva_offset(offset):
    with open(OFFSET_FILE, "w", encoding="utf-8") as file:
        file.write(str(offset))


def invia_messaggio_telegram(chat_id, messaggio):
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN mancante.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": messaggio,
            "disable_web_page_preview": False
        },
        timeout=30
    )

    if response.status_code == 200:
        print(f"Messaggio Telegram inviato a {chat_id}.")
    else:
        print(f"Errore invio Telegram a {chat_id}:")
        print(response.text)


def gestisci_comandi_telegram():
    if not TELEGRAM_BOT_TOKEN:
        print("Comandi Telegram non configurati.")
        return

    iscritti = carica_iscritti()
    offset = leggi_offset()

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    params = {
        "offset": offset + 1,
        "timeout": 0
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        dati = response.json()
    except Exception as errore:
        print(f"Errore lettura comandi Telegram: {errore}")
        return

    aggiornamenti = dati.get("result", [])

    if not aggiornamenti:
        print("Nessun nuovo comando Telegram.")
        return

    nuovo_offset = offset

    for update in aggiornamenti:
        nuovo_offset = max(nuovo_offset, update.get("update_id", nuovo_offset))

        messaggio = update.get("message", {})
        testo = (messaggio.get("text") or "").strip().lower()
        chat = messaggio.get("chat", {})
        chat_id = str(chat.get("id"))

        if not chat_id or chat_id == "None":
            continue

        if testo in ["/start", "/subscribe"]:
            if chat_id not in iscritti:
                iscritti.append(chat_id)
                salva_iscritti(iscritti)
                invia_messaggio_telegram(
                    chat_id,
                    "Iscrizione attivata. Riceverai notifiche quando il bot trova voli sotto soglia."
                )
                print(f"Nuovo iscritto: {chat_id}")
            else:
                invia_messaggio_telegram(
                    chat_id,
                    "Sei già iscritto alle notifiche voli."
                )

        elif testo == "/unsubscribe":
            if chat_id in iscritti:
                iscritti.remove(chat_id)
                salva_iscritti(iscritti)
                invia_messaggio_telegram(
                    chat_id,
                    "Iscrizione rimossa. Non riceverai più notifiche voli."
                )
                print(f"Iscritto rimosso: {chat_id}")
            else:
                invia_messaggio_telegram(
                    chat_id,
                    "Non eri iscritto alle notifiche voli."
                )

    salva_offset(nuovo_offset)


def invia_notifica_a_tutti(messaggio):
    iscritti = carica_iscritti()

    if TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID not in iscritti:
        iscritti.append(str(TELEGRAM_CHAT_ID))

    if not iscritti:
        print("Nessun iscritto Telegram a cui inviare notifiche.")
        return

    for chat_id in iscritti:
        invia_messaggio_telegram(chat_id, messaggio)


def get_trip_periods():
    periods = []

    if TRIP_PERIODS_RAW:
        raw_periods = TRIP_PERIODS_RAW.split(",")

        for raw_period in raw_periods:
            raw_period = raw_period.strip()

            if ":" not in raw_period:
                print(f"Periodo ignorato, formato non valido: {raw_period}")
                continue

            departure, return_date = raw_period.split(":", 1)
            departure = departure.strip()
            return_date = return_date.strip()

            if departure and return_date:
                periods.append((departure, return_date))

    if not periods and DEPARTURE_DATE and RETURN_DATE:
        periods.append((DEPARTURE_DATE, RETURN_DATE))

    return periods


def crea_link_google_flights(origin, destination, departure_date, return_date):
    testo = f"{origin} to {destination} {departure_date} {return_date}"
    query = urllib.parse.quote(testo)
    return f"https://www.google.com/travel/flights?q={query}"


def cerca_voli(origin, destination, departure_date, return_date):
    params = {
        "engine": "google_flights",
        "api_key": SERPAPI_KEY,
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "return_date": return_date,
        "adults": ADULTS,
        "currency": CURRENCY,
        "hl": "it",
        "gl": "it",
        "type": "1"
    }

    response = requests.get(SERPAPI_URL, params=params, timeout=60)

    if response.status_code != 200:
        print(f"\nErrore su {origin} → {destination}")
        print(f"Periodo: {departure_date} → {return_date}")
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


def crea_testo_volo(origin, destination, departure_date, return_date, volo):
    prezzo = volo["price"]
    scali = conta_scali(volo)
    link = crea_link_google_flights(origin, destination, departure_date, return_date)

    testo = (
        f"Volo trovato sotto soglia\n\n"
        f"Periodo: {departure_date} → {return_date}\n"
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


def stampa_risultato(origin, destination, departure_date, return_date, volo):
    prezzo = volo["price"]
    scali = conta_scali(volo)

    print("\n" + "=" * 60)
    print(f"Periodo: {departure_date} → {return_date}")
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
        print(f"Partenza: {partenza.get('name', 'N/D')} - {partenza.get('time', 'N/D')}")
        print(f"Arrivo: {arrivo.get('name', 'N/D')} - {arrivo.get('time', 'N/D')}")
        print()


def main():
    gestisci_comandi_telegram()

    trip_periods = get_trip_periods()

    print("DEBUG VARIABILI")
    print("SERPAPI_KEY presente =", bool(SERPAPI_KEY))
    print("TELEGRAM_BOT_TOKEN presente =", bool(TELEGRAM_BOT_TOKEN))
    print("TELEGRAM_CHAT_ID presente =", bool(TELEGRAM_CHAT_ID))
    print("ORIGINS =", repr(ORIGINS))
    print("DESTINATIONS =", repr(DESTINATIONS))
    print("DEPARTURE_DATE =", repr(DEPARTURE_DATE))
    print("RETURN_DATE =", repr(RETURN_DATE))
    print("TRIP_PERIODS =", repr(trip_periods))
    print("ADULTS =", repr(ADULTS))
    print("CURRENCY =", repr(CURRENCY))
    print("MAX_PRICE =", repr(MAX_PRICE))
    print("ISCRITTI TELEGRAM =", repr(carica_iscritti()))

    print("\nAvvio controllo prezzi voli")
    print(f"Adulti: {ADULTS}")
    print(f"Soglia prezzo: {MAX_PRICE} {CURRENCY}")

    if not SERPAPI_KEY:
        print("ERRORE: SERPAPI_KEY mancante")
        return

    if not trip_periods:
        print("ERRORE: nessun periodo valido configurato")
        return

    for departure_date, return_date in trip_periods:
        print("\n" + "#" * 60)
        print(f"Controllo periodo: {departure_date} → {return_date}")

        for origin in ORIGINS:
            for destination in DESTINATIONS:
                print("\n" + "-" * 60)
                print(f"Controllo {origin} → {destination}")

                try:
                    dati = cerca_voli(origin, destination, departure_date, return_date)
                    volo = estrai_volo_piu_economico(dati)

                    if volo:
                        stampa_risultato(origin, destination, departure_date, return_date, volo)

                        prezzo = volo["price"]

                        if prezzo <= MAX_PRICE:
                            messaggio = crea_testo_volo(
                                origin,
                                destination,
                                departure_date,
                                return_date,
                                volo
                            )
                            invia_notifica_a_tutti(messaggio)
                    else:
                        print("Nessun volo trovato.")

                except Exception as errore:
                    print(f"Errore su {origin} → {destination}: {errore}")


if __name__ == "__main__":
    main()
