import logging
from datetime import datetime
from pathlib import Path

from src.chart import ChartCreator
from src.demo_data import DemoDataProvider
from src.exporter import CsvExporter, ExcelExporter, JsonExporter
from src.fetcher import StockDataFetcher
from src.processor import StockDataProcessor

LOGGER = logging.getLogger(__name__)


class App:
    """Orchestriert Abruf, Verarbeitung, Auswertung und Ausgabe."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.fetcher = StockDataFetcher(retries=config["retries"])
        self.processor = StockDataProcessor(
            min_volume=config["min_volume"],
            sort_by=config["sort_by"],
        )
        self.excel_exporter = ExcelExporter()
        self.csv_exporter = CsvExporter()
        self.json_exporter = JsonExporter()
        self.chart_creator = ChartCreator()
        self.demo_provider = DemoDataProvider()

    def run(self, demo: bool = False, with_chart: bool = True):
        """Fuehrt den kompletten Ablauf aus.

        Rueckgabe: erzeugte Dateien, Fehlerhinweise und die Kennzahlen.
        """
        symbols = self.config["symbols"]
        # Ein Zeitstempel fuer alle Dateien eines Laufs, damit sie zusammengehoeren.
        self.stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if demo:
            LOGGER.info("Demo-Modus: es werden feste Beispieldaten verwendet.")
            quotes = self.demo_provider.get_data(symbols)
            errors: list[str] = []
        else:
            LOGGER.info("Abruf von %s Symbolen ueber die Yahoo-Finance-API.", len(symbols))
            quotes, errors = self.fetcher.fetch_many(symbols)

        prepared_quotes = self.processor.process(quotes)
        summary = self.processor.summarize(prepared_quotes)

        files: dict[str, str] = {}
        files["excel"] = self.excel_exporter.export(prepared_quotes, summary, self._path("xlsx"))
        files["csv"] = self.csv_exporter.export(prepared_quotes, self._path("csv"))
        files["json"] = self.json_exporter.export(prepared_quotes, summary, self._path("json"))
        if with_chart:
            files["diagramm"] = self.chart_creator.create(prepared_quotes, self._path("png"))

        return files, errors, summary

    def _path(self, extension: str) -> str:
        """Baut den Ausgabepfad; der Zeitstempel verhindert das Ueberschreiben."""
        name = f"{self.config['basename']}_{self.stamp}.{extension}"
        return str(Path(self.config["output_dir"]) / name)
