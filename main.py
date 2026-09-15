import argparse
import logging
import sys
from pathlib import Path

from src.app import App
from src.config import ConfigError, load_config
from src.logger import setup_logging

BASE_DIR = Path(__file__).resolve().parent
LOGGER = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Boersendaten abrufen, auswerten und als Excel, CSV, JSON und Diagramm speichern",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", default=str(BASE_DIR / "config.json"), help="Pfad zur Konfigurationsdatei")
    parser.add_argument("--symbols", nargs="+", help="Ticker-Symbole (ueberschreibt die Konfiguration)")
    parser.add_argument("--output-dir", help="Ausgabeverzeichnis (ueberschreibt die Konfiguration)")
    parser.add_argument("--min-volume", type=int, help="Mindesthandelsvolumen als Filter")
    parser.add_argument(
        "--sort-by",
        choices=["symbol", "change_percent", "volume", "volatility"],
        help="Sortierkriterium der Ausgabe",
    )
    parser.add_argument("--demo", action="store_true", help="feste Demo-Daten statt Live-API verwenden")
    parser.add_argument("--no-chart", action="store_true", help="kein PNG-Diagramm erzeugen")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def apply_overrides(config: dict, args: argparse.Namespace) -> dict:
    """Kommandozeilenparameter haben Vorrang vor der Konfigurationsdatei."""
    if args.symbols:
        config["symbols"] = [symbol.strip().upper() for symbol in args.symbols]
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.min_volume is not None:
        config["min_volume"] = args.min_volume
    if args.sort_by:
        config["sort_by"] = args.sort_by
    return config


def print_summary(summary) -> None:
    """Gibt die Kennzahlen des Laufs auf der Konsole aus."""
    print("\nAuswertung:")
    print(f"  Wertpapiere:              {summary.count}")
    print(f"  Im Plus / Im Minus:       {summary.gainers} / {summary.losers}")
    print(f"  Durchschnitt:             {summary.average_change_percent:+.2f} %")
    if summary.best:
        print(f"  Tagesbester:              {summary.best.symbol} ({summary.best.change_percent:+.2f} %)")
    if summary.worst:
        print(f"  Tagesschlechtester:       {summary.worst.symbol} ({summary.worst.change_percent:+.2f} %)")
    if summary.most_volatile:
        print(
            f"  Hoechste Handelsspanne:   {summary.most_volatile.symbol} "
            f"({summary.most_volatile.day_range_percent:.2f} %)"
        )


def main() -> int:
    args = parse_args()

    try:
        config = load_config(args.config if Path(args.config).exists() else None)
    except ConfigError as exc:
        print(f"Konfigurationsfehler: {exc}")
        return 1

    config = apply_overrides(config, args)
    log_file = str(Path(config["output_dir"]) / "boersendaten.log")
    setup_logging(args.log_level, log_file)
    LOGGER.info("Programmstart (Demo-Modus: %s)", args.demo)

    app = App(config)

    try:
        files, errors, summary = app.run(demo=args.demo, with_chart=not args.no_chart)
    except (ValueError, RuntimeError, ConnectionError) as exc:
        LOGGER.error("Verarbeitung abgebrochen: %s", exc)
        return 1
    except OSError as exc:
        LOGGER.error("Datei konnte nicht geschrieben werden: %s", exc)
        return 1

    print("\nErzeugte Dateien:")
    for label, path in files.items():
        print(f"  {label:10} {path}")

    print_summary(summary)

    if errors:
        print("\nHinweise:")
        for error in errors:
            print(f"  - {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
