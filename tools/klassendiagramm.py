#!/usr/bin/env python3
"""Erzeugt das Klassendiagramm (docs/klassendiagramm.png) mit Graphviz."""

from pathlib import Path

from graphviz import Digraph

FONT = "Helvetica"


def record(title: str, stereotype: str, attributes: list[str], methods: list[str]) -> str:
    """Baut eine UML-Klassenbox als HTML-Tabelle."""
    head = f'<B>{title}</B>'
    if stereotype:
        head = f'<FONT POINT-SIZE="9">&#171;{stereotype}&#187;</FONT><BR/>' + head

    rows = [f'<TR><TD BGCOLOR="#1F4E78"><FONT COLOR="white">{head}</FONT></TD></TR>']
    for block in (attributes, methods):
        if block:
            content = "<BR ALIGN=\"LEFT\"/>".join(block) + '<BR ALIGN="LEFT"/>'
            rows.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{content}</TD></TR>')

    return "<<TABLE BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"0\" CELLPADDING=\"5\">" + "".join(rows) + "</TABLE>>"


graph = Digraph("klassendiagramm", format="png")
graph.attr(rankdir="TB", splines="polyline", nodesep="0.5", ranksep="0.9", bgcolor="white")
graph.attr("node", shape="plaintext", fontname=FONT, fontsize="10")
graph.attr("edge", fontname=FONT, fontsize="9", color="#40525F")

# -- Einstieg und Steuerung --------------------------------------------------
graph.node("main", record("main.py", "Modul", [], [
    "parse_args() : Namespace",
    "apply_overrides(config, args) : dict",
    "print_summary(summary)",
    "main() : int",
]))

graph.node("config", record("config.py", "Modul", ["DEFAULT_CONFIG : dict", "ALLOWED_SORT_KEYS : tuple"], [
    "load_config(path) : dict",
    "validate(config) : dict",
]))

graph.node("logger", record("logger.py", "Modul", [], ["setup_logging(level, log_file) : Logger"]))

graph.node("app", record("App", "", [
    "config : dict",
    "fetcher : StockDataFetcher",
    "processor : StockDataProcessor",
    "excel_exporter : ExcelExporter",
    "csv_exporter : CsvExporter",
    "json_exporter : JsonExporter",
    "chart_creator : ChartCreator",
    "demo_provider : DemoDataProvider",
], [
    "run(demo, with_chart) : tuple",
    "- _path(extension) : str",
]))

# -- Datenbeschaffung --------------------------------------------------------
graph.node("fetcher", record("StockDataFetcher", "", ["retries : int", "retry_delay : float"], [
    "fetch_many(symbols) : (list, list)",
    "fetch_one(symbol) : StockQuote",
    "- _request(symbol) : StockQuote",
]))

graph.node("demo", record("DemoDataProvider", "", ["TEMPLATE : dict"], ["get_data(symbols) : list"]))

# -- Verarbeitung ------------------------------------------------------------
graph.node("processor", record("StockDataProcessor", "", ["min_volume : int", "sort_by : str"], [
    "process(quotes) : list",
    "sort(quotes) : list",
    "summarize(quotes) : MarketSummary",
]))

# -- Modelle -----------------------------------------------------------------
graph.node("quote", record("StockQuote", "dataclass", [
    "symbol : str",
    "name : str",
    "current_price : float",
    "day_high : float",
    "day_low : float",
    "open_price : float",
    "previous_close : float",
    "volume : int",
    "currency : str",
    "fetched_at : datetime",
], [
    "+ change_absolute : float",
    "+ change_percent : float",
    "+ day_range : float",
    "+ day_range_percent : float",
]))

graph.node("summary", record("MarketSummary", "dataclass", [
    "count : int",
    "gainers : int",
    "losers : int",
    "unchanged : int",
    "average_change_percent : float",
    "total_volume : int",
    "best : StockQuote",
    "worst : StockQuote",
    "most_volatile : StockQuote",
], []))

# -- Ausgabe -----------------------------------------------------------------
graph.node("excel", record("ExcelExporter", "", ["HEADERS : list"], [
    "export(quotes, summary, path) : str",
    "- _apply_number_format(...)",
    "- _add_summary_sheet(...)",
    "- _add_chart_sheet(...)",
]))
graph.node("csv", record("CsvExporter", "", ["HEADERS : list"], ["export(quotes, path) : str"]))
graph.node("json", record("JsonExporter", "", [], ["export(quotes, summary, path) : str"]))
graph.node("chart", record("ChartCreator", "", [], ["create(quotes, path) : str"]))

# -- Beziehungen -------------------------------------------------------------
graph.edge("main", "config", label="nutzt", style="dashed", arrowhead="vee")
graph.edge("main", "logger", label="nutzt", style="dashed", arrowhead="vee")
graph.edge("main", "app", label="erzeugt", arrowhead="vee")

for target in ("fetcher", "demo", "processor", "excel", "csv", "json", "chart"):
    # Aggregation: App haelt die Komponenten (gefuellte Raute an der Ganzheit)
    graph.edge("app", target, dir="back", arrowtail="diamond", arrowhead="none")

graph.edge("fetcher", "quote", label="erzeugt", style="dashed", arrowhead="vee")
graph.edge("demo", "quote", label="erzeugt", style="dashed", arrowhead="vee")
graph.edge("processor", "quote", label="filtert / sortiert", style="dashed", arrowhead="vee")
graph.edge("processor", "summary", label="erzeugt", style="dashed", arrowhead="vee")
graph.edge("summary", "quote", label="referenziert", style="dashed", arrowhead="vee", constraint="false")

# Ebenen festlegen, damit das Diagramm kompakt und auf A4 lesbar bleibt.
# Unsichtbare Kanten schieben zwei Exporter eine Ebene tiefer, damit das
# Diagramm nicht zu breit und auf A4 noch lesbar wird.
graph.edge("excel", "json", style="invis")
graph.edge("csv", "chart", style="invis")

for group in (("fetcher", "demo", "processor", "excel", "csv"), ("json", "chart"), ("quote", "summary")):
    with graph.subgraph() as same:
        same.attr(rank="same")
        for node in group:
            same.node(node)

target_dir = Path(__file__).resolve().parent.parent / "docs"
target_dir.mkdir(parents=True, exist_ok=True)
output = graph.render(filename=str(target_dir / "klassendiagramm"), cleanup=True)
print(output)
