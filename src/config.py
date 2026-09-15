import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "symbols": ["AAPL", "MSFT", "NVDA", "SAP.DE", "NESN.SW", "UBSG.SW"],
    "min_volume": 0,
    "sort_by": "change_percent",
    "output_dir": "output",
    "basename": "boersendaten",
    "retries": 2,
}

ALLOWED_SORT_KEYS = ("symbol", "change_percent", "volume", "volatility")


class ConfigError(ValueError):
    """Die Konfigurationsdatei ist fehlerhaft oder unvollstaendig."""


def load_config(path: str | None) -> dict:
    """Laedt die JSON-Konfiguration und ergaenzt fehlende Werte mit den Vorgaben."""
    config = dict(DEFAULT_CONFIG)

    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Konfigurationsdatei nicht gefunden: {config_path}")
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Ungueltiges JSON in {config_path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{config_path} muss ein JSON-Objekt enthalten.")
        config.update(data)
        LOGGER.info("Konfiguration geladen: %s", config_path)

    return validate(config)


def validate(config: dict) -> dict:
    """Prueft die Werte, damit Fehler frueh und mit klarer Meldung auffallen."""
    symbols = config.get("symbols")
    if not isinstance(symbols, list) or not symbols:
        raise ConfigError("'symbols' muss eine nicht leere Liste von Kuerzeln sein.")
    config["symbols"] = [str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()]
    if not config["symbols"]:
        raise ConfigError("'symbols' enthaelt keine gueltigen Kuerzel.")

    try:
        config["min_volume"] = int(config.get("min_volume", 0))
    except (TypeError, ValueError) as exc:
        raise ConfigError("'min_volume' muss eine ganze Zahl sein.") from exc
    if config["min_volume"] < 0:
        raise ConfigError("'min_volume' darf nicht negativ sein.")

    if config.get("sort_by") not in ALLOWED_SORT_KEYS:
        raise ConfigError(f"'sort_by' muss einer der Werte {ALLOWED_SORT_KEYS} sein.")

    try:
        config["retries"] = int(config.get("retries", 2))
    except (TypeError, ValueError) as exc:
        raise ConfigError("'retries' muss eine ganze Zahl sein.") from exc
    if config["retries"] < 0:
        raise ConfigError("'retries' darf nicht negativ sein.")

    config["output_dir"] = str(config.get("output_dir") or "output")
    config["basename"] = str(config.get("basename") or "boersendaten")
    return config
