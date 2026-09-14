import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Backend ohne Bildschirm, damit auch Cron-Jobs Diagramme erzeugen koennen

import matplotlib.pyplot as plt  # noqa: E402

from src.models import StockQuote  # noqa: E402

LOGGER = logging.getLogger(__name__)


class ChartCreator:
    """Erzeugt ein Balkendiagramm der Tagesveraenderung als PNG."""

    def create(self, quotes: list[StockQuote], output_path: str) -> str:
        if not quotes:
            raise ValueError("Keine Daten fuer das Diagramm vorhanden.")

        ordered = sorted(quotes, key=lambda quote: quote.change_percent)
        symbols = [quote.symbol for quote in ordered]
        changes = [quote.change_percent for quote in ordered]
        colors = ["#C0453B" if change < 0 else "#4C9A5B" for change in changes]

        height = max(3.0, 0.4 * len(ordered) + 1.5)
        figure, axes = plt.subplots(figsize=(9, height))
        bars = axes.barh(symbols, changes, color=colors, edgecolor="#333333", linewidth=0.4)

        axes.axvline(0, color="#333333", linewidth=0.8)
        axes.set_xlabel("Veraenderung gegenueber Vortag in %")
        axes.set_title(f"Tagesveraenderung  |  Stand {ordered[0].fetched_at:%d.%m.%Y %H:%M}")
        axes.grid(axis="x", linestyle=":", alpha=0.5)
        axes.set_axisbelow(True)

        # Beschriftung direkt am Balken, damit die Werte ablesbar sind.
        offset = (max(changes) - min(changes) or 1) * 0.02
        for bar, change in zip(bars, changes):
            position = bar.get_width() + (offset if change >= 0 else -offset)
            axes.text(
                position,
                bar.get_y() + bar.get_height() / 2,
                f"{change:+.2f} %",
                va="center",
                ha="left" if change >= 0 else "right",
                fontsize=8,
            )

        axes.margins(x=0.15)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.tight_layout()
        figure.savefig(output, dpi=130)
        plt.close(figure)

        LOGGER.info("Diagramm geschrieben: %s", output)
        return str(output)
