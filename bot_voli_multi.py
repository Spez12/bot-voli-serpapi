import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

ORIGINS = os.getenv("ORIGINS", "FCO").split(",")
DESTINATIONS = os.getenv("DESTINATIONS", "LHR").split(",")

DEPARTURE_DATE = os.getenv("DEPARTURE_DATE")
RETURN_DATE = os.getenv("RETURN_DATE")

ADULTS = int(os.getenv("ADULTS") or "2")
CURRENCY = os.getenv("CURRENCY", "EUR")
MAX_PRICE = float(os.getenv("MAX_PRICE") or "250")

SERPAPI_URL = "https://serpapi.com/search.json"


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
    response.raise_for_status()
    return response.json()


def mostra_debug(dati):
    print("\n--- DEBUG RISPOSTA SERPAPI ---")

    if "error" in dati:
        print("ERRORE SERPAPI:")
        print(dati["error"])
        return

    print("Chiavi ricevute dalla risposta:")
    print(list(dati.keys()))

    if "search_metadata" in dati:
        print("\nStato ricerca:")
        print(dati["search_metadata"].get("status"))

    if "best_flights" in dati:
        print(f"best_flights trovati: {len(dati['best_flights'])}")
    else:
        print("best_flights non presente.")

    if "other_flights" in dati:
        print(f"other_flights trovati: {len(dati['other_flights'])}")
    else:
        print("other_flights non presente.")

    print("--- FINE DEBUG ---\n")


def estrai_prezzo_minore(dati):
    voli = []

    voli.extend(dati.get("best_flights", []))
    voli.extend(dati.get("other_flights", []))

    voli_con_prezzo = []

    for volo in voli:
        prezzo = volo.get("price")

        if isinstance(prezzo, (int, float)):
            voli_con_prezzo.append(volo)

    if not voli_con_prezzo:
        return None

    return min(voli_con_prezzo, key=lambda volo: volo["price"])


def stampa_risultato(origin, destination, volo):
    prezzo = volo["price"]

    print("-" * 60)
    print(f"Rotta: {origin} → {destination}")
    print(f"Prezzo totale per {ADULTS} persone: {prezzo} {CURRENCY}")

    if prezzo <= MAX_PRICE:
        print("OFFERTA INTERESSANTE: prezzo sotto la soglia.")
    else:
        print("Prezzo sopra la soglia.")

    for tratta in volo.get("flights", []):
        compagnia = tratta.get("airline", "Compagnia non disponibile")
        partenza = tratta.get("departure_airport", {})
        arrivo = tratta.get("arrival_airport", {})

        print()
        print(f"Compagnia: {compagnia}")
        print(f"Partenza: {partenza.get('name')} - {partenza.get('time')}")
        print(f"Arrivo: {arrivo.get('name')} - {arrivo.get('time')}")


def main():
    if not SERPAPI_KEY:
        print("Errore: manca SERPAPI_KEY nel file .env")
        return

    print("Avvio controllo prezzi voli con SerpApi...")
    print(f"Partenza: {DEPARTURE_DATE}")
    print(f"Ritorno: {RETURN_DATE}")
    print(f"Adulti: {ADULTS}")
    print(f"Soglia prezzo: {MAX_PRICE} {CURRENCY}")

    for origin in ORIGINS:
        origin = origin.strip().upper()

        for destination in DESTINATIONS:
            destination = destination.strip().upper()

            print("-" * 60)
            print(f"Controllo {origin} → {destination}...")

            try:
                dati = cerca_voli(origin, destination)
                mostra_debug(dati)

                volo_migliore = estrai_prezzo_minore(dati)

                if volo_migliore:
                    stampa_risultato(origin, destination, volo_migliore)
                else:
                    print(f"{origin} → {destination}")
                    print("Nessun volo con prezzo leggibile trovato.")

            except Exception as errore:
                print(f"Errore su {origin} → {destination}")
                print(errore)


if __name__ == "__main__":
    main()