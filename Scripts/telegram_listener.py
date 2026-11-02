import os
import json
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import trafilatura
from pypdf import PdfReader

# --- ZUGANGSDATEN ---
BOT_TOKEN = "----"
OPENAI_API_KEY = "----"
CHAT_ID = "----"  # Nur deine Telegram Chat-ID verarbeiten

# Pfade
BASE_DIR = r"./Obsidian_Vault_Example"
OBSIDIAN_INBOX = os.path.join(BASE_DIR, "KI_Knowledge_Base", "00_Inbox")
HISTORY_FILE = os.path.join(BASE_DIR, "processed_links.json")

# --- HELPER FÜR DEDUPLIZIERUNG ---
def is_already_processed(identifier):
    """Prüft, ob eine URL oder ein Dokument bereits verarbeitet wurde."""
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return identifier in data
    except Exception:
        return False

def mark_as_processed(identifier):
    """Speichert einen verarbeiteten Eintrag in der Historie."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    
    if identifier not in data:
        data.append(identifier)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Historie: {e}")

# --- KI-VERARBEITUNG ---
def process_content_with_ai(title, raw_text, source_type):
    print(f"🤖 Analysiere {source_type} mit KI auf Deutsch...")
    
    prompt = f"""
Du bist ein exzellenter KI-Forschungsassistent und Knowledge Manager. Analysiere den folgenden Inhalt ({source_type}) und bereite ihn komplett auf Deutsch für eine Obsidian-Wissensdatenbank auf.

Titel / Kontext: {title}
Inhalt:
{raw_text[:4000]}

Erstelle eine strukturierte Markdown-Antwort auf Deutsch mit exakt folgenden Abschnitten:
1. **Titel (übersetzt/prägnant)**: Gib der Notiz ganz oben einen prägnanten deutschen Titel (als Markdown-Überschrift #).
2. ## 📌 Executive Summary
   - Eine prägnante Zusammenfassung des Inhalts in 2-3 Sätzen auf Deutsch.
3. ## 💡 Key Insights
   - 3 bis 4 wichtigste Erkenntnisse als Stichpunkte auf Deutsch.
4. ## 🔬 Fachbegriffe & Definitionen
   - Relevante Fachbegriffe aus dem Text kurz und verständlich auf Deutsch definiert (falls vorhanden, sonst "Keine spezifischen Begriffe").

Antworte NUR mit dem Markdown-Inhalt für den Textkörper (kein Code-Block drumherum, direkt der Text).
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
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"❌ OpenAI Fehler: {response.text}")
        return f"# {title}\n\n## 📌 Inhalt\n{raw_text}"

# --- HANDLER FÜR TELEGRAM ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        return

    text = update.message.text
    document = update.message.document

    # 1. FALL: TEXT ODER URL
    if text:
        if text.startswith("http://") or text.startswith("https://"):
            url = text.strip()
            
            if is_already_processed(url):
                await update.message.reply_text("⚠️ **Duplikat erkannt!**\nDiese URL wurde bereits in deiner Wissensdatenbank erfasst.")
                return

            await update.message.reply_text("🌐 Neue URL erkannt! Lese Webseiten-Inhalt aus...")
            downloaded = trafilatura.fetch_url(url)
            extracted_text = trafilatura.extract(downloaded) if downloaded else "Konnte Text nicht extrahieren."
            title = url.split("//")[-1].split("/")[0]
            
            ai_content = process_content_with_ai(title, extracted_text, "Web-Artikel")
            source_link = url
            mark_as_processed(url)
            
        else:
            await update.message.reply_text("📝 Text (Copy & Paste) erkannt! Analysiere...")
            title = text.split("\n")[0][:40]
            ai_content = process_content_with_ai(title, text, "Quick-Paste")
            source_link = "Telegram Quick-Capture"

        # In Obsidian speichern
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
        filename = f"{date_str}_{safe_title}.md"
        
        os.makedirs(OBSIDIAN_INBOX, exist_ok=True)
        file_path = os.path.join(OBSIDIAN_INBOX, filename)
        
        markdown_content = f"""---
aliases: []
tags: [ki-radar, telegram-capture, unreviewed]
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
source: "{source_link}"
---

{ai_content}

---
*Erfasst via Telegram Zwei-Wege-Kommunikation und auf Deutsch aufbereitet.*
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        await update.message.reply_text(f"✅ Erfolgreich in Obsidian gespeichert!\n📂 Ordner: 00_Inbox\n📄 Datei: {filename}")

    # 2. FALL: DOKUMENT (PDF)
    elif document:
        file_name = document.file_name
        if not file_name.lower().endswith(".pdf"):
            await update.message.reply_text("⚠️ Aktuell werden nur PDF-Dokumente unterstützt.")
            return

        # Duplikat-Check über Dateinamen
        if is_already_processed(file_name):
            await update.message.reply_text(f"⚠️ **Duplikat erkannt!**\nDie PDF '{file_name}' wurde bereits verarbeitet.")
            return

        await update.message.reply_text(f"📁 PDF '{file_name}' empfangen! Lese Dokument aus...")
        
        # Datei von Telegram herunterladen
        file_obj = await context.bot.get_file(document.file_id)
        temp_pdf_path = f"temp_{file_name}"
        await file_obj.download_to_drive(temp_pdf_path)

        # Text mit pypdf extrahieren
        extracted_text = ""
        try:
            reader = PdfReader(temp_pdf_path)
            for page in reader.pages:
                text_page = page.extract_text()
                if text_page:
                    extracted_text += text_page + "\n"
        except Exception as e:
            print(f"❌ PDF Lesefehler: {e}")
            extracted_text = "Konnte PDF-Inhalt nicht auslesen."
        
        # Temporäre Datei wieder löschen
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

        title = file_name.replace(".pdf", "").replace(".PDF", "")
        ai_content = process_content_with_ai(title, extracted_text, "PDF-Dokument")
        
        mark_as_processed(file_name)

        # In Obsidian speichern
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        safe_title = "".join([c if c.isalnum() else "_" for c in title])[:50]
        filename = f"{date_str}_{safe_title}.md"
        
        os.makedirs(OBSIDIAN_INBOX, exist_ok=True)
        file_path = os.path.join(OBSIDIAN_INBOX, filename)
        
        markdown_content = f"""---
aliases: []
tags: [ki-radar, telegram-pdf, unreviewed]
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
source: "Telegram PDF: {file_name}"
---

{ai_content}

---
*Erfasst via Telegram PDF-Upload und auf Deutsch aufbereitet.*
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        await update.message.reply_text(f"✅ PDF erfolgreich in Obsidian gespeichert!\n📂 Ordner: 00_Inbox\n📄 Datei: {filename}")

if __name__ == "__main__":
    print("🤖 Telegram Listener mit PDF-Support gestartet...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    
    app.run_polling(drop_pending_updates=True)