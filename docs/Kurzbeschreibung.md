# Kurzbeschreibung: Webautomatisierung mittels Scripting

**Projekt:** Automatisierter Abruf und Auswertung von Börsendaten
**Sprache / Werkzeuge:** Python 3.12, yfinance, openpyxl, matplotlib

## 1. Problemstellung

Wer mehrere Wertpapiere beobachtet, ruft die Kurse üblicherweise einzeln auf
einer Finanzseite ab und überträgt sie von Hand in eine Tabelle. Das kostet
täglich Zeit, ist fehleranfällig und liefert keine Auswertung: Wie hat sich
der überwachte Korb insgesamt entwickelt? Welches Papier ist am stärksten
gefallen? Wo war die Tagesschwankung am grössten?

Ziel der Arbeit ist ein Skript, das diesen Ablauf vollständig automatisiert:
Daten abrufen, prüfen, filtern, auswerten und in Formaten ablegen, die sowohl
ein Mensch (Excel, Diagramm) als auch ein Folgeprozess (CSV, JSON) weiter
verwenden kann. Das Skript soll sich ohne Codeänderung an eine andere
Beobachtungsliste anpassen lassen und unbeaufsichtigt als geplante Aufgabe
laufen können.

## 2. Vorgehen

**Werkzeugwahl.** Für Kursdaten existiert mit Yahoo Finance eine etablierte
Schnittstelle, die über die Bibliothek `yfinance` ansprechbar ist. Eine API ist
hier dem Scraping klar vorzuziehen: Die Daten kommen strukturiert und typisiert
zurück, es gibt keine Abhängigkeit vom HTML-Aufbau der Seite, und rechtlich ist
der Weg über die dafür vorgesehene Schnittstelle unbedenklich. Scraping wäre
nur sinnvoll, wenn keine API verfügbar wäre.

**Aufbau.** Das Programm ist in Schichten getrennt, jede Klasse hat eine
Aufgabe:

| Schicht | Klasse | Aufgabe |
| --- | --- | --- |
| Konfiguration | `load_config` | JSON-Datei lesen und prüfen |
| Abruf | `StockDataFetcher` | API-Aufruf je Symbol, Wiederholversuche |
| Verarbeitung | `StockDataProcessor` | Validierung, Filterung, Sortierung, Kennzahlen |
| Ausgabe | `ExcelExporter`, `CsvExporter`, `JsonExporter`, `ChartCreator` | vier Ausgabeformate |
| Ablauf | `App` | Orchestrierung der Schritte |

Diese Trennung macht die Verarbeitung unabhängig von der Datenquelle testbar:
Der Demo-Modus speist dieselbe Verarbeitungskette mit festen Beispieldaten und
kommt ohne Internet aus.

**Verarbeitung.** Aus Kurs und Vortagesschluss werden die absolute und die
prozentuale Tagesveränderung berechnet, aus Tageshoch und Tagestief die
Handelsspanne als Volatilitätsmass. Datensätze mit nicht positivem Kurs oder
widersprüchlichen Werten werden verworfen, ein konfigurierbarer Mindestumsatz
filtert markteng gehandelte Papiere heraus. Anschliessend wird nach dem
gewählten Kriterium sortiert und über den gesamten Korb ausgewertet: Anzahl
Gewinner und Verlierer, durchschnittliche Veränderung, Gesamtvolumen sowie
Tagesbester, Tagesschlechtester und volatilstes Papier.

**Fehlerbehandlung.** Verbindungsfehler und Timeouts lösen Wiederholversuche
mit Wartezeit aus. Schlägt ein einzelnes Symbol dauerhaft fehl, läuft der
Durchgang mit den übrigen weiter und meldet das Problem am Schluss als Hinweis;
erst wenn kein einziger Datensatz zustande kommt, bricht das Programm mit
Rückgabewert 1 ab. Unvollständige API-Antworten werden erkannt, ein fehlender
Vortagesschluss durch den Eröffnungskurs ersetzt. Alle Schritte werden auf der
Konsole und in einer rotierenden Logdatei protokolliert.

## 3. Ergebnisse

Ein Lauf erzeugt vier Dateien mit gemeinsamem Zeitstempel:

- **Excel-Mappe** mit den Blättern *Kursdaten*, *Kennzahlen* und
  *Visualisierung*. Veränderung und Handelsspanne sind als Formeln hinterlegt,
  bleiben in Excel also nachvollziehbar. Eine Farbskala unterscheidet Gewinner
  von Verlierern, Datenbalken zeigen die Volatilität, ein Balkendiagramm die
  Tagesveränderung je Symbol.
- **CSV** mit Semikolon und UTF-8-BOM, direkt in Excel lesbar.
- **JSON** mit Kursdaten und Kennzahlen für Folgeskripte.
- **PNG-Diagramm** der Tagesveränderung, grün/rot eingefärbt und beschriftet.

Der Demo-Lauf über acht Wertpapiere liefert reproduzierbar vier Gewinner und
vier Verlierer bei einer durchschnittlichen Veränderung von +0.20 %, als
Tagesbester NVDA (+4.85 %), als Schlechtester TSLA (−5.88 %), das zugleich mit
6.87 % die grösste Handelsspanne aufweist.

Vierzehn Unit-Tests prüfen Kennzahlenberechnung, Filter, Sortierung,
Konfigurationsvalidierung und alle drei Exportformate; sie laufen ohne
Netzzugriff. Über einen Cron-Job beziehungsweise die Windows-Aufgabenplanung
lässt sich das Skript täglich nach Börsenschluss ausführen, sodass die
Auswertung ohne weiteres Zutun bereitliegt.

**Mögliche Erweiterungen:** Versand des Berichts per E-Mail, Schwellenwert-
Alarme bei starken Kursbewegungen sowie eine Datenbank, die die Läufe
historisiert und Verläufe über mehrere Tage darstellbar macht.
