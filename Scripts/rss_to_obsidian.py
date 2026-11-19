import os
import json
import feedparser
import requests
from datetime import datetime
import trafilatura
from difflib import SequenceMatcher

# --- ZUGANGSDATEN ---
OPENAI_API_KEY = "----"
CHAT_ID = "----"

# Ausgewogene RSS-Quellen: Von verständlichen Einsteiger-News bis zu praktischen AI-Engineer-Quellen
RSS_FEEDS = [
    # 1. Die verständlichen Branchen-News (Perfekt zum Mitkommen ohne Fachchinesisch)
    {"name": "The Batch (DeepLearning.AI)", "url": "https://www.deeplearning.ai/the-batch/feed/"},
    
    # 2. Die Praxis-Klassiker & Tools (Hands-on für Macher)
    {"name": "Simon Willison AI Blog", "url": "https://simonwillison.net/atom/entries/"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    
    # 3. Tiefergehendes Verständnis (Wenn du wissen willst, wie es unter der Haube tickt)
    {"name": "Ahead of AI (Raschka)", "url": "https://magazine.sebastianraschka.com/feed"},
    
    # 4. Große Modell-Anbieter (Direkt von der Quelle)
    {"name": "OpenAI News", "url": "https://openai.com/news/rss.xml"},
    
    # %: Neuer Tutorial- & Evergreen-Feed
    {"name": "Lilian Weng AI Deep Dives", "url": "https://lilianweng.github.io/index.xml"},
]

# Pfade & Ordnerstruktur
BASE_DIR = r"./Obsidian_Vault_Example"  # Pfad zum eigenen Obsidian-Vault eintragen
DIR_NEWS = os.path.join(BASE_DIR, "KI_Knowledge_Base", "02_News_Events")
DIR_EVERGREEN = os.path.join(BASE_DIR, "KI_Knowledge_Base", "01_Evergreen_Knowledge")
HISTORY_FILE = os.path.join(BASE_DIR, "processed_links.json")

def is_already_processed(url):
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return url in data
    except Exception:
        return False

def mark_as_processed(url):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    
    if url not in data:
        data.append(url)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"❌ Telegram Fehler: {e}")

def check_evergreen_duplicate(new_title, threshold=0.6):
    """
    Prüft, ob im Evergreen-Ordner bereits eine Notiz existiert,
    deren Titel dem neuen Titel stark ähnelt (Ähnlichkeit > threshold).
    """
    if not os.path.exists(DIR_EVERGREEN):
        return False, None
    
    existing_files = os.listdir(DIR_EVERGREEN)
    for filename in existing_files:
        if filename.endswith(".md"):
            # Dateinamen-Format: YYYY-MM-DD_HH-MM_Bereinigter_Titel.md
            # Wir extrahieren den Titel-Teil nach dem Zeitstempel
            parts = filename.split("_", 2)
            if len(parts) >= 3:
                clean_name = parts[2].replace(".md", "").replace("_", " ").lower()
                similarity = SequenceMatcher(None, new_title.lower(), clean_name).ratio()
                if similarity >= threshold:
                    return True, filename
                    
    return False, None

def process_rss_feeds():
    print("📡 Starte Abruf aller RSS-Feeds mit Smart Routing & Evergreen-Check...")
    
    for feed_info in RSS_FEEDS:
        feed_name = feed_info["name"]
        feed_url = feed_info["url"]
        print(f"🔍 Prüfe Feed: {feed_name}")
        
        parsed_feed = feedparser.parse(feed_url)
        
        for entry in parsed_feed.entries[:1]:
            entry_url = entry.link
            entry_title = entry.title
            
            if is_already_processed(entry_url):
                print(f"ℹ️ Übersprungen (URL bekannt): {entry_title}")
                continue
            
            print(f"🆕 Neuer Artikel: {entry_title}")
            downloaded = trafilatura.fetch_url(entry_url)
            article_text = trafilatura.extract(downloaded) if downloaded else None
            
            if not article_text:
                article_text = getattr(entry, 'summary', 'Kein Text extrahierbar.')
            
            prompt = f"""
Du bist ein exzellenter KI-Forschungsassistent und Knowledge Manager. Analysiere den folgenden Web-Volltext aus einem RSS-Feed ({feed_name}) für eine Obsidian-Wissensdatenbank.

Titel: {entry_title}
Volltext:
{article_text[:4000]}

Aufgabe 1: Erstelle eine strukturierte Markdown-Antwort auf Deutsch mit exakt folgenden Abschnitten:
1. **Titel (übersetzt/prägnant)**: Gib der Notiz einen prägnanten deutschen Titel (als Markdown-Überschrift #).
2. ## 📌 Executive Summary
   - Eine prägnante Zusammenfassung in 2-3 Sätzen auf Deutsch.
3. ## 💡 Key Insights
   - 3 bis 4 wichtigste Erkenntnisse als Stichpunkte auf Deutsch.
4. ## 🔬 Fachbegriffe & Definitionen
   - Relevante Fachbegriffe kurz und verständlich auf Deutsch definiert (oder "Keine").

Aufgabe 2 (Smart Routing):
Entscheide, ob dieser Inhalt ein zeitgebundenes Release/eine News oder zeitloses Grundlagenwissen (Evergreen) ist.
Schreibe ganz am Ende deines Outputs in einer neuen Zeile exakt eines der folgenden Wörter:
KATEGORIE: NEWS
oder
KATEGORIE: EVERGREEN
"""

            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            
            if response.status_code == 200:
                ai_response_full = response.json()["choices"][0]["message"]["content"]
                
                target_dir = DIR_NEWS
                category_label = "News"
                
                if "KATEGORIE: EVERGREEN" in ai_response_full:
                    target_dir = DIR_EVERGREEN
                    category_label = "Evergreen Knowledge"
                    ai_content = ai_response_full.replace("KATEGORIE: EVERGREEN", "").strip()
                else:
                    ai_content = ai_response_full.replace("KATEGORIE: NEWS", "").strip()
                
                # --- EVERGREEN DUPLIKAT-CHECK ---
                if target_dir == DIR_EVERGREEN:
                    is_dup, existing_file = check_evergreen_duplicate(entry_title, threshold=0.55)
                    if is_dup:
                        print(f"⚠️ Evergreen-Duplikat erkannt! Ähnlich zu: {existing_file}")
                        print(f"ℹ️ Überspringe Speicherung, um Redundanz im Wissensnetz zu vermeiden: {entry_title}")
                        mark_as_processed(entry_url) # Trotzdem als verarbeitet markieren, damit er nicht endlos looped
                        send_telegram_message(f"🛡️ *Evergreen-Duplikat abgefangen!*\n\n📌 *{entry_title}*\nÄhnlich zu bestehender Notiz: `{existing_file}` (Übersprungen)")
                        continue
                
                # In Obsidian speichern
                date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
                safe_title = "".join([c if c.isalnum() else "_" for c in entry_title])[:50]
                filename = f"{date_str}_{safe_title}.md"
                
                os.makedirs(target_dir, exist_ok=True)
                file_path = os.path.join(target_dir, filename)
                
                markdown_content = f"""---
aliases: []
tags: [ki-radar, rss-feed, {category_label.lower().replace(" ", "-")}]
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
source: "{entry_url}"
---

{ai_content}

---
*Automatisch erfasst, via Smart Routing einsortiert und auf Redundanz geprüft ({feed_name}).*
"""
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                mark_as_processed(entry_url)
                folder_name = os.path.basename(target_dir)
                send_telegram_message(f"🧠 *Smart Routing & Evergreen-Check erfolgreich!*\n\n📌 *{entry_title}*\n📂 Ziel: `{folder_name}`\n📄 `{filename}`")
                print(f"✅ Eingesortiert in [{folder_name}]: {entry_title}")
            else:
                print(f"❌ OpenAI API Fehler: {response.text}")

if __name__ == "__main__":
    process_rss_feeds()