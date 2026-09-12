from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockQuote:
    """Ein Kursdatensatz zu einem Wertpapier."""

    symbol: str
    name: str
    current_price: float
    day_high: float
    day_low: float
    open_price: float
    previous_close: float
    volume: int
    currency: str
    fetched_at: datetime

    @property
    def change_absolute(self) -> float:
        """Veränderung gegenüber dem Schlusskurs des Vortages."""
        return round(self.current_price - self.previous_close, 4)

    @property
    def change_percent(self) -> float:
        """Veränderung gegenüber dem Vortag in Prozent."""
        if self.previous_close == 0:
            return 0.0
        return round((self.current_price - self.previous_close) / self.previous_close * 100, 2)

    @property
    def day_range(self) -> float:
        """Handelsspanne des Tages (Tageshoch minus Tagestief)."""
        return round(self.day_high - self.day_low, 4)

    @property
    def day_range_percent(self) -> float:
        """Handelsspanne in Prozent des Tagestiefs (Mass fuer die Volatilitaet)."""
        if self.day_low == 0:
            return 0.0
        return round((self.day_high - self.day_low) / self.day_low * 100, 2)


@dataclass
class MarketSummary:
    """Aggregierte Kennzahlen ueber alle abgerufenen Wertpapiere."""

    count: int
    gainers: int
    losers: int
    unchanged: int
    average_change_percent: float
    total_volume: int
    best: StockQuote | None
    worst: StockQuote | None
    most_volatile: StockQuote | None
