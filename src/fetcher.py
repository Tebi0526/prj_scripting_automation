import logging
import time
from datetime import datetime

import yfinance as yf

from src.models import StockQuote

LOGGER = logging.getLogger(__name__)


class StockDataFetcher:
    """Ruft Boersendaten ueber yfinance / Yahoo Finance ab."""

    def __init__(self, retries: int = 2, retry_delay: float = 1.5) -> None:
        self.retries = retries
        self.retry_delay = retry_delay

    def fetch_many(self, symbols: list[str]) -> tuple[list[StockQuote], list[str]]:
        cleaned_symbols = [symbol.strip().upper() for symbol in symbols if symbol and symbol.strip()]
        if not cleaned_symbols:
            raise ValueError("Es wurde kein gueltiges Wertpapierkuerzel angegeben.")

        quotes: list[StockQuote] = []
        errors: list[str] = []

        for symbol in cleaned_symbols:
            try:
                quotes.append(self.fetch_one(symbol))
                LOGGER.info("Daten fuer %s erfolgreich abgerufen.", symbol)
            except Exception as exc:  # zentrale Fehlerbehandlung pro Symbol
                LOGGER.warning("Abruf fuer %s fehlgeschlagen: %s", symbol, exc)
                errors.append(f"{symbol}: {exc}")

        if not quotes:
            raise RuntimeError("Es konnten keine Boersendaten abgerufen werden.")

        return quotes, errors

    def fetch_one(self, symbol: str) -> StockQuote:
        """Ruft ein einzelnes Symbol ab und wiederholt den Versuch bei Fehlern."""
        last_error: Exception | None = None

        for attempt in range(1, self.retries + 2):
            try:
                return self._request(symbol)
            except ValueError:
                raise  # unvollstaendige Antwort: ein zweiter Versuch bringt nichts
            except Exception as exc:
                last_error = exc
                LOGGER.debug("Versuch %s fuer %s fehlgeschlagen: %s", attempt, symbol, exc)
                if attempt <= self.retries:
                    time.sleep(self.retry_delay)

        raise ConnectionError(
            f"API-Aufruf nach {self.retries + 1} Versuchen fehlgeschlagen ({last_error})."
        )

    def _request(self, symbol: str) -> StockQuote:
        ticker = yf.Ticker(symbol)

        try:
            info = ticker.info or {}
        except Exception as exc:
            raise ConnectionError("API-Aufruf fehlgeschlagen oder keine Internetverbindung verfuegbar.") from exc

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
        day_low = info.get("dayLow") or info.get("regularMarketDayLow")
        open_price = info.get("open") or info.get("regularMarketOpen")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        volume = info.get("volume") or info.get("regularMarketVolume")
        name = info.get("shortName") or info.get("longName") or symbol
        currency = info.get("currency") or "USD"

        required_values = [current_price, day_high, day_low, open_price, volume]
        if any(value is None for value in required_values):
            raise ValueError("Ungueltige oder unvollstaendige API-Antwort.")

        if previous_close is None:
            # Nicht jedes Papier liefert den Vortagesschluss (z. B. am ersten
            # Handelstag). Dann dient der Eroeffnungskurs als Bezugsgroesse.
            LOGGER.info("%s: kein Vortagesschluss geliefert, es wird der Eroeffnungskurs verwendet.", symbol)
            previous_close = open_price

        return StockQuote(
            symbol=symbol,
            name=name,
            current_price=float(current_price),
            day_high=float(day_high),
            day_low=float(day_low),
            open_price=float(open_price),
            previous_close=float(previous_close),
            volume=int(volume),
            currency=str(currency).upper(),
            fetched_at=datetime.now(),
        )
