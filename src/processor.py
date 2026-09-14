import logging

from src.models import MarketSummary, StockQuote

LOGGER = logging.getLogger(__name__)


class StockDataProcessor:
    """Prueft, filtert und sortiert die abgerufenen Daten und berechnet Kennzahlen."""

    def __init__(self, min_volume: int = 0, sort_by: str = "change_percent") -> None:
        self.min_volume = min_volume
        self.sort_by = sort_by

    def process(self, quotes: list[StockQuote]) -> list[StockQuote]:
        if not quotes:
            raise ValueError("Es liegen keine Daten zur Verarbeitung vor.")

        valid_quotes: list[StockQuote] = []
        for quote in quotes:
            if quote.current_price <= 0:
                LOGGER.info("%s verworfen: Kurs ist nicht positiv.", quote.symbol)
                continue
            if quote.day_high < quote.day_low:
                LOGGER.info("%s verworfen: Tageshoch liegt unter dem Tagestief.", quote.symbol)
                continue
            if quote.volume < self.min_volume:
                LOGGER.info(
                    "%s gefiltert: Handelsvolumen %s liegt unter dem Grenzwert %s.",
                    quote.symbol,
                    quote.volume,
                    self.min_volume,
                )
                continue
            valid_quotes.append(quote)

        if not valid_quotes:
            raise ValueError("Die Ergebnismenge ist leer.")

        LOGGER.info("%s von %s Datensaetzen weiterverarbeitet.", len(valid_quotes), len(quotes))
        return self.sort(valid_quotes)

    def sort(self, quotes: list[StockQuote]) -> list[StockQuote]:
        """Sortiert die Datensaetze nach dem konfigurierten Kriterium."""
        keys = {
            "symbol": lambda item: item.symbol,
            "change_percent": lambda item: -item.change_percent,
            "volume": lambda item: -item.volume,
            "volatility": lambda item: -item.day_range_percent,
        }
        key = keys.get(self.sort_by)
        if key is None:
            LOGGER.warning("Unbekanntes Sortierkriterium '%s', es wird nach Symbol sortiert.", self.sort_by)
            key = keys["symbol"]
        return sorted(quotes, key=key)

    def summarize(self, quotes: list[StockQuote]) -> MarketSummary:
        """Berechnet die Kennzahlen ueber alle verarbeiteten Wertpapiere."""
        if not quotes:
            raise ValueError("Fuer die Auswertung liegen keine Daten vor.")

        gainers = [quote for quote in quotes if quote.change_percent > 0]
        losers = [quote for quote in quotes if quote.change_percent < 0]
        average = sum(quote.change_percent for quote in quotes) / len(quotes)

        return MarketSummary(
            count=len(quotes),
            gainers=len(gainers),
            losers=len(losers),
            unchanged=len(quotes) - len(gainers) - len(losers),
            average_change_percent=round(average, 2),
            total_volume=sum(quote.volume for quote in quotes),
            best=max(quotes, key=lambda item: item.change_percent),
            worst=min(quotes, key=lambda item: item.change_percent),
            most_volatile=max(quotes, key=lambda item: item.day_range_percent),
        )
