# 🧬 AI Knowledge & Intelligence Radar (Autonomes Second Brain in Obsidian)

Ein vollautonomes, produktionsreifes Knowledge-Management-System in Obsidian zur automatisierten Erfassung, intelligenten Aufbereitung und strukturierten Ablage von KI-Wissen aus RSS-Feeds und Telegram.

---

## 🚀 Executive Summary & Projektziel

Das Ziel dieses Projekts war die Entwicklung eines vollautonomen, produktionsreifen Knowledge-Management-Systems direkt in Obsidian. Statt sich in der täglichen Informationsflut von KI-News zu verlieren, sollte ein zentraler, intelligenter „Ingest-Hub“ entstehen. Dieser sammelt Rohdaten aus handverlesenen RSS-Feeds, Telegram-Chats und PDFs, extrahiert die Volltexte, lässt sich durch `gpt-4o-mini` aufbereiten, sortiert sie intelligent vor (Smart Routing) und schützt das System aktiv vor Redundanzen. 

> **Transparenzhinweis & Entwicklungsansatz:** Dieses System wurde nach dem „AI-First-Builder“-Prinzip konzipiert und umgesetzt. Als Architekt des Workflows lag der Fokus auf der Konzeption des Datenflusses, der Systemlogik (Smart Routing, Deduplizierung) und der nahtlosen Integration von APIs und lokalen Dateisystemen. Der Einsatz moderner KI-Assistenten diente dabei als hocheffizienter Entwicklungshebel – ein Beweis dafür, wie man komplexe Automatisierungen pragmatisch, schnell und mit klarem Blick für den echten Nutzwert realisiert.

*Hinweis zum Setup:* Alle persönlichen API-Keys und lokalen Systempfade wurden im Code bereinigt und durch Platzhalter ersetzt. Die Historien-Datei (`processed_links.json`) wird standardmäßig als leere Liste im Repository bereitgestellt, um einen sauberen Start zu garantieren.

---

## 🛠️ Der Tech-Stack

Das System setzt auf einen schlanken, performanten und vollständig lokal kontrollierten Python-Stack:

* **Programmiersprache:** Python (für Automatisierungs- und Parsing-Skripte)
* **Web Scraping & Extraction:** `trafilatura` (zuverlässige Extraction sauberer Artikel-Volltexte aus URLs unter Umgehung von Boilerplate)
* **Dokumenten-Ingestion:** `pypdf` (lokales Parsen von PDFs und Whitepapern)
* **Künstliche Intelligenz:** OpenAI `gpt-4o-mini` (für semantische Synthese, Executive Summaries, Key Insights und Klassifizierung)
* **Schnittstellen & Benachrichtigungen:** Telegram Bot API (für mobile Ingestion und Echtzeit-Statusmeldungen)
* **Wissensbasis & Struktur:** Obsidian (lokales Markdown-basiertes Second Brain mit automatisiertem Frontmatter-Management)

---

## 🏗️ Architektur & Datenfluss (Von A bis Z)

Die Pipeline arbeitet im Hintergrund und folgt einem modularen 4-Schichten-Modell:

### Schritt A: Multi-Channel Ingestion Hub
* **RSS-Feeds:** Sechs handverlesene, ausgewogene Top-Quellen decken sowohl aktuelle Branchen-News als auch tiefe technische Deep-Dives ab (*The Batch, Simon Willison, Hugging Face, Ahead of AI, OpenAI News, Lilian Weng*).
* **Telegram-Listener:** Ein permanent im Hintergrund laufender Bot (`telegram_listener.py`) nimmt geteilte Links oder Dokumente mobil entgegen und füttert das System.

![RSS Script Execution Log](Pictures/rss-script-execution-log.png)

### Schritt B: Globaler Duplikats-Schutz (Der Türsteher)
Ein zentrales `processed_links.json`-Register speichert jede erfolgreich verarbeitete URL. Dies verhindert Endlosschleifen und sorgt dafür, dass Artikel niemals doppelt eingelesen werden.

### Schritt C: KI-Synthese & Smart Routing (Das Gehirn)
`gpt-4o-mini` analysiert den Volltext und generiert eine strukturierte Markdown-Notiz mit folgenden Sektionen:
1. Prägnanter deutscher Titel
2. 📌 **Executive Summary** (Zusammenfassung in 2-3 Sätzen)
3. 💡 **Key Insights** (Die wichtigsten Kernpunkte als Bullet Points)
4. 🔬 **Fachbegriffe & Definitionen** (Verständliche Erklärungen für Einsteiger)

Smart Routing: Die KI klassifiziert den Inhalt am Ende des Prompts automatisch in zwei Kategorien:
* `KATEGORIE: NEWS` $\rightarrow$ Zielordner: `KI_Knowledge_Base/02_News_Events`
* `KATEGORIE: EVERGREEN` $\rightarrow$ Zielordner: `KI_Knowledge_Base/01_Evergreen_Knowledge`

### Schritt D: Evergreen-Deduplizierung & Ablage
Handelt es sich um einen Evergreen-Artikel, prüft ein maßgeschneiderter String-Ähnlichkeits-Abgleich (via Python `difflib`), ob im entsprechenden Ordner bereits eine thematisch identische Notiz existiert (Schwellenwert-Prüfung). Bei einem Treffer wird die Erstellung abgefangen, um Redundanzen im Wissensnetz zu verhindern. Andernfalls wird die Datei mit sauberem YAML-Frontmatter im Zielverzeichnis gespeichert.

![Obsidian Vault Structure](Pictures/obsidian-vault-structure.png)

---

## 💡 Key Challenges & Lösungen

* **Herausforderung 1: Informationsüberflutung & Fachchinesisch**
  * *Lösung:* Ein speziell optimierter System-Prompt, der technische Fachartikel so aufbereitet, dass Kernkonzepte auch für Einsteiger greifbar und direkt anwendbar werden.
* **Herausforderung 2: Unstrukturierte Inboxes & Vermischung von News und Konzepten**
  * *Lösung:* Implementierung des Smart Routings. Flüchtige Release-Meldungen landen getrennt von zeitlosem Grundlagenwissen in dezidierten Ordnern.
* **Herausforderung 3: Redundante Wissensartikel im Second Brain**
  * *Lösung:* Ein automatisierter Titel- und Inhaltsabgleich vor dem Speichern von Evergreen-Notizen, der das System langfristig schlank, übersichtlich und frei von Dubletten hält.

![Obsidian Generated Note Preview](Pictures/obsidian-generated-note-preview.png)

---

## 🚀 Fazit & Ausblick

Das Projekt beweist, wie sich moderne LLM-APIs, Web-Scraping und lokale Dateisysteme (Obsidian) zu einem mächtigen, autarken Werkzeug verbinden lassen. Das System läuft vollautomatisch im Hintergrund und liefert täglich präzise aufbereitetes, redundanzfreies Wissen – die perfekte Basis für kontinuierliches Lernen im KI-Sektor.

---

## 📂 Repository-Struktur

```text
├── Scripts/
│   ├── rss_to_obsidian.py          # Haupt-Pipeline für RSS-Ingestion & Smart Routing
│   └── telegram_listener.py        # Hintergrund-Bot für mobile Link-Erfassung
├── Pictures/
│   ├── rss-script-execution-log.png
│   ├── obsidian-vault-structure.png
│   └── obsidian-generated-note-preview.png
├── processed_links.json            # Zentrales Register zur Duplikatsvermeidung (leer initialisiert)
├── requirements.txt                # Python-Abhängigkeiten
└── README.md                       # Projektdokumentation
