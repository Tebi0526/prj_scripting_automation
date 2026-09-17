# Börsendaten-Automatisierung (Praxisarbeit Webautomatisierung)

Python-Skript, das Kursdaten über die Yahoo-Finance-API abruft, sie filtert,
sortiert und auswertet und das Ergebnis als Excel-Mappe, CSV, JSON und
PNG-Diagramm speichert.

Die Arbeit baut auf der bestehenden Hausarbeit "Python-Anwendung für
Börsendaten" auf und erweitert sie um die Anforderungen der Praxisarbeit:
Konfigurationsdatei, Filterung, Kennzahlen, mehrere Ausgabeformate,
Logging, Fehlerbehandlung, geplante Ausführung und Unit-Tests.

## Installation

```bash
pip install -r requirements.txt
```

Getestet mit Python 3.12.

## Start

```bash
python main.py --demo      # ohne Internet, feste Beispieldaten
python main.py             # Live-Abruf mit den Symbolen aus config.json
```

Weitere Parameter:

| Parameter | Wirkung |
| --- | --- |
| `--config PFAD` | andere Konfigurationsdatei verwenden |
| `--symbols AAPL MSFT` | Symbole der Konfiguration überschreiben |
| `--output-dir PFAD` | Ausgabeverzeichnis überschreiben |
| `--min-volume 1000000` | Wertpapiere mit kleinerem Handelsvolumen herausfiltern |
| `--sort-by symbol\|change_percent\|volume\|volatility` | Sortierkriterium |
| `--demo` | feste Demo-Daten statt Live-API |
| `--no-chart` | kein PNG-Diagramm erzeugen |
| `--log-level DEBUG` | ausführlichere Protokollierung |

Rückgabewerte: `0` bei Erfolg, `1` bei Abbruch (nützlich für geplante Tasks).

## Konfiguration (`config.json`)

```json
{
  "symbols": ["AAPL", "MSFT", "NVDA", "TSLA", "SAP.DE", "NESN.SW", "UBSG.SW", "ZURN.SW"],
  "min_volume": 0,
  "sort_by": "change_percent",
  "output_dir": "output",
  "basename": "boersendaten",
  "retries": 2
}
```

Fehlende Werte werden durch Vorgaben ergänzt, ungültige Werte führen zu einer
verständlichen Fehlermeldung statt zu einem Absturz.

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `main.py` | Programmeinstieg, Kommandozeilenparameter, Konsolenausgabe |
| `src/config.py` | Konfiguration laden und prüfen |
| `src/logger.py` | Protokollierung auf Konsole und in rotierende Logdatei |
| `src/app.py` | Orchestrierung des Ablaufs |
| `src/fetcher.py` | API-Abruf über yfinance inkl. Wiederholversuchen |
| `src/processor.py` | Validierung, Filterung, Sortierung, Kennzahlen |
| `src/exporter.py` | Ausgabe als Excel, CSV und JSON |
| `src/chart.py` | Balkendiagramm mit matplotlib |
| `src/demo_data.py` | feste Beispieldaten für den Demo-Modus |
| `tests/` | Unit-Tests ohne Netzzugriff |

## Ausgabe

Pro Lauf entstehen im Ausgabeverzeichnis vier Dateien mit gemeinsamem
Zeitstempel im Namen:

- `boersendaten_JJJJMMTT_HHMMSS.xlsx` – Blätter *Kursdaten*, *Kennzahlen* und
  *Visualisierung*; Veränderung und Handelsspanne sind als Excel-Formeln
  hinterlegt, bedingte Formatierung hebt Gewinner, Verlierer und hohe
  Volatilität hervor
- `... .csv` – Semikolon und UTF-8-BOM, öffnet sich in Excel direkt korrekt
- `... .json` – Kursdaten und Kennzahlen für die Weiterverarbeitung
- `... .png` – Balkendiagramm der Tagesveränderung

Zusätzlich schreibt das Skript `output/boersendaten.log` (rotierend, max. 4
Dateien à 256 KB).

## Geplante Ausführung

Linux / Raspberry Pi (werktags um 18:10 Uhr):

```cron
10 18 * * 1-5 cd /pfad/zum/projekt && /usr/bin/python3 main.py >> output/cron.log 2>&1
```

Windows (Aufgabenplanung):

```powershell
$action  = New-ScheduledTaskAction -Execute "python.exe" -Argument "main.py" -WorkingDirectory "C:\Pfad\zum\Projekt"
$trigger = New-ScheduledTaskTrigger -Daily -At 18:10
Register-ScheduledTask -TaskName "Boersendaten" -Action $action -Trigger $trigger
```

## Tests

```bash
python -m pytest tests -q
```

14 Tests decken Kennzahlenberechnung, Filterung, Sortierung, Konfigurations-
prüfung und die drei Exportformate ab. Sie laufen ohne Internetverbindung.

## Fehlerbehandlung

- Wiederholversuche mit Wartezeit bei Verbindungs- und Timeout-Fehlern
- Ein fehlerhaftes Symbol bricht den Lauf nicht ab, sondern wird am Ende als
  Hinweis ausgegeben
- Unvollständige API-Antworten werden erkannt und verworfen
- Fehlt der Vortagesschluss, dient der Eröffnungskurs als Bezugsgrösse
- Ungültige Konfiguration und nicht schreibbare Ausgabepfade werden mit
  Klartextmeldung und Rückgabewert 1 quittiert
