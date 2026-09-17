#!/usr/bin/env python3
"""Erzeugt das Sequenzdiagramm (docs/sequenzdiagramm.png) mit matplotlib."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrow, FancyBboxPatch, Rectangle  # noqa: E402

DARK = "#1F4E78"
LINE = "#40525F"
NOTE = "#FFF6D9"

PARTICIPANTS = [
    "main.py",
    "config.py",
    "App",
    "StockDataFetcher",
    "Yahoo Finance\n(yfinance)",
    "StockDataProcessor",
    "ExcelExporter\nCsvExporter\nJsonExporter",
    "ChartCreator",
]

# (Absender, Empfaenger, Beschriftung, Rueckgabe?)
MESSAGES = [
    (0, 1, "load_config(pfad)", False),
    (1, 0, "geprüfte Konfiguration (dict)", True),
    (0, 2, "run(demo, with_chart)", False),
    (2, 3, "fetch_many(symbole)", False),
    (3, 4, "Ticker.info je Symbol", False),
    (4, 3, "Kursdaten (JSON)", True),
    (3, 2, "list[StockQuote], Fehlerliste", True),
    (2, 5, "process(quotes)", False),
    (5, 2, "geprüfte, gefilterte, sortierte Liste", True),
    (2, 5, "summarize(quotes)", False),
    (5, 2, "MarketSummary", True),
    (2, 6, "export(quotes, summary, pfad)", False),
    (6, 2, "Pfade zu xlsx / csv / json", True),
    (2, 7, "create(quotes, pfad)", False),
    (7, 2, "Pfad zum PNG", True),
    (2, 0, "Dateien, Hinweise, Kennzahlen", True),
]

STEP = 1.0
TOP = 0.0
BOTTOM = TOP - STEP * (len(MESSAGES) + 1.2)

figure, axes = plt.subplots(figsize=(15.5, 11))
axes.set_xlim(-0.75, len(PARTICIPANTS) - 0.25)
axes.set_ylim(BOTTOM - 1.4, 2.0)
axes.axis("off")

# -- Kopfzeilen und Lebenslinien --------------------------------------------
for index, name in enumerate(PARTICIPANTS):
    box = FancyBboxPatch(
        (index - 0.42, 0.75),
        0.84,
        0.95,
        boxstyle="round,pad=0.04",
        linewidth=1.1,
        edgecolor=DARK,
        facecolor=DARK if index in (0, 2) else "white",
    )
    axes.add_patch(box)
    axes.text(
        index,
        1.22,
        name,
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color="white" if index in (0, 2) else DARK,
    )
    axes.plot([index, index], [0.72, BOTTOM], linestyle=(0, (4, 4)), color=LINE, linewidth=0.8, zorder=1)

# -- Aktivierungsbalken ------------------------------------------------------
def activation(index: int, start: int, end: int) -> None:
    """Zeichnet den Aktivitätsbalken eines Teilnehmers über mehrere Schritte."""
    y_top = TOP - STEP * start + 0.18
    y_bottom = TOP - STEP * end - 0.18
    axes.add_patch(
        Rectangle(
            (index - 0.07, y_bottom),
            0.14,
            y_top - y_bottom,
            facecolor="#D9EAF7",
            edgecolor=DARK,
            linewidth=0.7,
            zorder=2,
        )
    )


activation(0, 0, 16)
activation(1, 0, 1)
activation(2, 2, 15)
activation(3, 3, 6)
activation(4, 4, 5)
activation(5, 7, 8)
activation(5, 9, 10)
activation(6, 11, 12)
activation(7, 13, 14)

# -- Nachrichten -------------------------------------------------------------
for step, (sender, receiver, label, is_return) in enumerate(MESSAGES):
    y = TOP - STEP * step
    direction = 1 if receiver > sender else -1
    start = sender + direction * 0.08
    end = receiver - direction * 0.08

    axes.add_patch(
        FancyArrow(
            start,
            y,
            end - start,
            0,
            width=0.006,
            head_width=0.11,
            head_length=0.11,
            length_includes_head=True,
            color=LINE,
            linestyle="dashed" if is_return else "solid",
            zorder=3,
        )
    )
    axes.text(
        (start + end) / 2,
        y + 0.14,
        label,
        ha="center",
        va="bottom",
        fontsize=8,
        color="#22313B",
        style="italic" if is_return else "normal",
    )

# -- Anmerkungen -------------------------------------------------------------
def note(x: float, y: float, text: str, width: float = 2.5) -> None:
    axes.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=7.8,
        color="#4A3B00",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=NOTE, edgecolor="#D9C27A", linewidth=0.8),
    )


note(1.0, TOP - STEP * 2.55, "Mit --demo liefert DemoDataProvider\nfeste Beispieldaten; die Schritte 4 bis 6\nentfallen, der Ablauf bleibt gleich.")
note(5.55, TOP - STEP * 4.55, "Fehler je Symbol: Wiederholversuch,\ndann Vermerk in der Fehlerliste –\nder Lauf wird fortgesetzt.")
note(1.0, TOP - STEP * 8.5, "Filter: Kurs positiv, Hoch/Tief plausibel,\nMindestvolumen. Kennzahlen: Gewinner,\nVerlierer, Durchschnitt, Extremwerte.")

axes.text(
    (len(PARTICIPANTS) - 1) / 2,
    BOTTOM - 0.75,
    "Anschliessend gibt main.py die Kennzahlen und die Dateipfade auf der Konsole aus "
    "und beendet das Programm mit Rückgabewert 0 (bei Abbruch 1).",
    ha="center",
    va="center",
    fontsize=8.5,
    color=DARK,
)

axes.set_title("Sequenzdiagramm: Ablauf eines Programmlaufs", fontsize=13, fontweight="bold", color=DARK, pad=16)

target = Path(__file__).resolve().parent.parent / "docs" / "sequenzdiagramm.png"
target.parent.mkdir(parents=True, exist_ok=True)
figure.tight_layout()
figure.savefig(target, dpi=140, facecolor="white")
plt.close(figure)
print(target)
