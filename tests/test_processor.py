"""Tests fuer Verarbeitung, Kennzahlen und Export (laufen ohne Internet)."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ConfigError, validate  # noqa: E402
from src.demo_data import DemoDataProvider  # noqa: E402
from src.exporter import CsvExporter, ExcelExporter, JsonExporter  # noqa: E402
from src.models import StockQuote  # noqa: E402
from src.processor import StockDataProcessor  # noqa: E402

STAMP = datetime(2026, 3, 11, 17, 30, 0)


def quote(symbol="AAA", price=110.0, previous=100.0, high=112.0, low=108.0, volume=1000):
    return StockQuote(symbol, f"{symbol} AG", price, high, low, 109.0, previous, volume, "CHF", STAMP)


# -- Kennzahlen im Modell ----------------------------------------------------
def test_change_percent_wird_korrekt_berechnet():
    assert quote(price=110.0, previous=100.0).change_percent == 10.0
    assert quote(price=90.0, previous=100.0).change_percent == -10.0


def test_change_percent_faengt_division_durch_null_ab():
    assert quote(previous=0.0).change_percent == 0.0


def test_handelsspanne_in_prozent():
    assert quote(high=110.0, low=100.0).day_range_percent == 10.0


# -- Verarbeitung ------------------------------------------------------------
def test_negative_kurse_werden_verworfen():
    processor = StockDataProcessor()
    result = processor.process([quote("AAA"), quote("BBB", price=-5.0)])
    assert [item.symbol for item in result] == ["AAA"]


def test_volumenfilter_greift():
    processor = StockDataProcessor(min_volume=5000)
    result = processor.process([quote("AAA", volume=10000), quote("BBB", volume=100)])
    assert [item.symbol for item in result] == ["AAA"]


def test_leere_ergebnismenge_wirft_fehler():
    processor = StockDataProcessor(min_volume=99999)
    with pytest.raises(ValueError):
        processor.process([quote("AAA", volume=10)])


def test_sortierung_nach_veraenderung():
    processor = StockDataProcessor(sort_by="change_percent")
    result = processor.process([
        quote("AAA", price=101.0, previous=100.0),
        quote("BBB", price=120.0, previous=100.0),
    ])
    assert [item.symbol for item in result] == ["BBB", "AAA"]


def test_unbekanntes_sortierkriterium_faellt_auf_symbol_zurueck():
    processor = StockDataProcessor(sort_by="gibtsnicht")
    result = processor.process([quote("BBB"), quote("AAA")])
    assert [item.symbol for item in result] == ["AAA", "BBB"]


def test_kennzahlen():
    processor = StockDataProcessor()
    quotes = [
        quote("AAA", price=110.0, previous=100.0, high=115.0, low=100.0),
        quote("BBB", price=95.0, previous=100.0),
        quote("CCC", price=100.0, previous=100.0),
    ]
    summary = processor.summarize(quotes)
    assert (summary.count, summary.gainers, summary.losers, summary.unchanged) == (3, 1, 1, 1)
    assert summary.best.symbol == "AAA"
    assert summary.worst.symbol == "BBB"
    assert summary.most_volatile.symbol == "AAA"


# -- Konfiguration -----------------------------------------------------------
def test_konfiguration_lehnt_leere_symbolliste_ab():
    with pytest.raises(ConfigError):
        validate({"symbols": [], "sort_by": "symbol"})


def test_konfiguration_lehnt_falsches_sortierkriterium_ab():
    with pytest.raises(ConfigError):
        validate({"symbols": ["AAPL"], "sort_by": "unsinn"})


def test_konfiguration_normalisiert_symbole():
    config = validate({"symbols": [" aapl ", "msft"], "sort_by": "symbol"})
    assert config["symbols"] == ["AAPL", "MSFT"]


# -- Demo-Daten und Export ---------------------------------------------------
def test_demo_daten_unbekanntes_symbol():
    with pytest.raises(ValueError):
        DemoDataProvider().get_data(["GIBTSNICHT"])


def test_export_erzeugt_alle_dateien(tmp_path):
    processor = StockDataProcessor()
    quotes = processor.process(DemoDataProvider().get_data(["AAPL", "MSFT", "TSLA"]))
    summary = processor.summarize(quotes)

    xlsx = ExcelExporter().export(quotes, summary, str(tmp_path / "test.xlsx"))
    csv_file = CsvExporter().export(quotes, str(tmp_path / "test.csv"))
    json_file = JsonExporter().export(quotes, summary, str(tmp_path / "test.json"))

    assert Path(xlsx).exists() and Path(xlsx).stat().st_size > 0
    assert Path(csv_file).read_text(encoding="utf-8-sig").startswith("Symbol;")
    payload = json.loads(Path(json_file).read_text(encoding="utf-8"))
    assert payload["kennzahlen"]["anzahl"] == 3
    assert len(payload["kursdaten"]) == 3
