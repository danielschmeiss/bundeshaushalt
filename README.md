# Bundeshaushalt – Transparenz für alle

Interaktive Visualisierung des deutschen Bundeshaushalts 2020–2026. Ziel ist es, die Haushaltsdaten des Bundes für alle Bürgerinnen und Bürger verständlich und zugänglich zu machen.

**Live:** [danielschmeiss.github.io/bundeshaushalt](https://danielschmeiss.github.io/bundeshaushalt)

---

## Ansichten

| Tab | Inhalt |
|-----|--------|
| **Übersicht** | Gesamtausgaben und -einnahmen je Jahr, Entwicklung im Zeitverlauf, Aufschlüsselung nach Ministerium |
| **Ministerienvergleich** | Ausgaben mehrerer Ministerien gleichzeitig vergleichen |
| **Jahresdetails** | Alle Einzelpläne eines Haushaltsjahres als Balkendiagramm und Tabelle |
| **Suche** | Volltext-Suche über alle ~49.000 Haushaltspositionen, sortierbar nach allen Spalten |
| **Panorama** | Streamgraph der Haushaltsstruktur + Heatmap der jährlichen Veränderungen |
| **Ministerium-Zeitverlauf** | Entwicklung innerhalb eines Ministeriums nach Ausgabenart oder Kapitel |
| **Einnahmen** | Woher kommt das Geld? Steuerarten, Kreditaufnahme und EU-Mittel im Zeitverlauf, mit Bürger-Erklärungen |

## Datenquellen

Rohdaten: [bundeshaushalt.de](https://www.bundeshaushalt.de) (Bundesministerium der Finanzen)

| Datei | Jahr |
|-------|------|
| `hh_2020_utf8.csv` | 2020 |
| `hh_2021_n2_utf8.csv` | 2021 |
| `hh_2022_utf8.csv` | 2022 |
| `HH_2023.csv` | 2023 |
| `HH_2024_ALL.csv` | 2024 |
| `HH_2025_ALL.csv` | 2025 |
| `HH_2026_ALL.csv` | 2026 |

Die CSV-Dateien sind nicht im Repository enthalten (`.gitignore`). Die vorverarbeiteten JSON-Dateien unter `data/` werden mitgeliefert und reichen für den Betrieb der Seite aus.

## Lokale Entwicklung

**Voraussetzung:** Python 3

```bash
# Webserver starten (nötig wegen fetch() für JSON-Dateien)
python3 -m http.server 8080
# → http://localhost:8080
```

**Daten neu generieren** (nur wenn neue CSV-Dateien vorliegen):

```bash
python3 process_data.py
```

Das Skript liest alle CSVs, normalisiert Formatunterschiede zwischen den Jahren und schreibt vier JSON-Dateien:

| Datei | Inhalt | Größe |
|-------|--------|-------|
| `data/summary.json` | Jahrestotale + Ministeriumssummen | ~7 KB |
| `data/detail.json` | Aufschlüsselung je EP nach Kapitel und Ausgabenart | ~180 KB |
| `data/einnahmen.json` | Einnahmen nach Kategorie und Top-Steuerarten | ~3 KB |
| `data/titles.json` | Alle ~49.000 Einzeltitel | ~5,7 MB |

## Technischer Aufbau

- **Reines HTML/CSS/JS** – kein Framework, kein Build-Schritt
- **Chart.js 4.4.0** (CDN) für alle Diagramme
- **Lazy Loading**: `summary.json` beim Start, `titles.json` erst bei Suche, `detail.json` erst bei Ministerium-Zeitverlauf
- Alle Beträge sind **Sollwerte in Tausend Euro**

## Hinweise zur Interpretation

- **Ausgaben = Einnahmen** ist im deutschen Bundeshaushalt korrekt: Kreditaufnahme zählt als Einnahme.
- **EP 32 (Bundesschuld)** und **EP 60 (Allgemeine Finanzverwaltung)** enthalten Schuldenverwaltung und zentrale Steuereinnahmen – sie werden in manchen Ansichten standardmäßig ausgeblendet, da ihr Volumen die Fachministerien überdeckt.
- Die Einnahmen-Kategorien zeigen **Nettobeträge**: Der Bundesanteil an Gemeinschaftsteuern ist nach Abzug der Länderanteile ausgewiesen; EU-Eigenmittel-Zahlungen werden gegengerechnet.

## Lizenz

Daten: [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0)  
Code: MIT
