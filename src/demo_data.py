from datetime import datetime

from src.models import StockQuote

DEMO_TIMESTAMP = datetime(2026, 3, 11, 17, 30, 0)


class DemoDataProvider:
    """Liefert feste Beispieldaten fuer eine reproduzierbare Musterausgabe.

    Der Demo-Modus laeuft ohne Internet und erzeugt immer dieselbe Datei.
    Damit laesst sich die Verarbeitung unabhaengig von der API pruefen.
    """

    TEMPLATE = {
        "AAPL": StockQuote("AAPL", "Apple Inc.", 218.45, 220.10, 216.80, 217.35, 214.90, 54123456, "USD", DEMO_TIMESTAMP),
        "MSFT": StockQuote("MSFT", "Microsoft Corp.", 428.72, 431.55, 426.40, 427.10, 430.15, 23456789, "USD", DEMO_TIMESTAMP),
        "NVDA": StockQuote("NVDA", "NVIDIA Corp.", 142.18, 146.90, 139.55, 140.20, 135.60, 198345612, "USD", DEMO_TIMESTAMP),
        "SAP.DE": StockQuote("SAP.DE", "SAP SE", 186.25, 187.40, 184.95, 185.30, 188.05, 3123456, "EUR", DEMO_TIMESTAMP),
        "NESN.SW": StockQuote("NESN.SW", "Nestle SA", 79.86, 80.44, 79.52, 80.10, 80.02, 4210987, "CHF", DEMO_TIMESTAMP),
        "UBSG.SW": StockQuote("UBSG.SW", "UBS Group AG", 28.94, 29.31, 28.55, 28.62, 28.31, 8765432, "CHF", DEMO_TIMESTAMP),
        "TSLA": StockQuote("TSLA", "Tesla Inc.", 246.30, 259.80, 243.10, 257.45, 261.70, 112233445, "USD", DEMO_TIMESTAMP),
        "ZURN.SW": StockQuote("ZURN.SW", "Zurich Insurance Group AG", 552.40, 556.20, 549.80, 550.00, 551.00, 512345, "CHF", DEMO_TIMESTAMP),
    }

    def get_data(self, symbols: list[str]) -> list[StockQuote]:
        cleaned = [symbol.strip().upper() for symbol in symbols if symbol and symbol.strip()]
        if not cleaned:
            raise ValueError("Es wurde kein gueltiges Wertpapierkuerzel angegeben.")

        result = [self.TEMPLATE[symbol] for symbol in cleaned if symbol in self.TEMPLATE]
        if not result:
            verfuegbar = ", ".join(sorted(self.TEMPLATE))
            raise ValueError(f"Fuer die Demo sind nur folgende Symbole hinterlegt: {verfuegbar}")
        return result
