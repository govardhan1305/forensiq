# 🔍 ForensIQ — AI-Based Smart Forensic Intelligence System

> An AI-powered web application that helps users detect cyber threats (scams, phishing, fraud) by analysing digital evidence like messages, links, and screenshots.

---

## 📸 Features

| Feature | Description |
|---|---|
| 🔍 Message Analyzer | Detect scams, fraud, and phishing in any text |
| 🔗 Link Checker | Analyse URLs for phishing and malicious redirects |
| 🖼 Screenshot Analyzer | OCR extraction + AI analysis of uploaded images |
| 💼 Job Offer Detector | Spot fake job/recruitment scams |
| 🗂 Evidence Locker | Save all analysed items in local SQLite database |
| 📄 Complaint Generator | Generate formatted cybercrime complaint letters |
| 🤖 AI Cyber Assistant | Chat with CyberGuard AI for safety advice |
| 📊 Dashboard | Real-time stats, charts, and recent activity |
| 🔊 Voice Input | Speech-to-text → auto-analysis |
| 🌐 Multi-language | EN / Hindi toggle |
| 💡 Awareness Hub | AI-generated safety tips and threat guides |
| 🔎 Similar Scam Detection | Pattern matching against known scam database |

---

## ⚙️ Tech Stack

- **Backend**: Python 3.10+ / Flask 3.0
- **Database**: SQLite (auto-created on first run)
- **AI**: OpenAI GPT-3.5-turbo (with heuristic fallback if no key)
- **OCR**: pytesseract + Pillow (optional)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Chart.js
- **PDF**: fpdf2 (optional)

---

## 🚀 Quick Start

### 1. Clone / Extract the Project

```bash
cd forensiq
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-key-here
SECRET_KEY=change-this-in-production
FLASK_DEBUG=True
```

> **Note**: The app runs in **demo mode** (keyword-based heuristics) if no API key is provided. All other features work without an API key.

### 5. (Optional) Install Tesseract OCR

For screenshot text extraction:

**Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki  
**Ubuntu/Debian**: `sudo apt install tesseract-ocr`  
**Mac**: `brew install tesseract`

### 6. Run the Application

```bash
python app.py
```

Visit: **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
forensiq/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API keys)
├── README.md
│
├── database/
│   └── forensiq.db         # SQLite database (auto-created)
│
├── uploads/                # Uploaded screenshot files
│
├── templates/
│   ├── base.html           # Base layout with navbar/footer
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Dashboard with charts
│   ├── analyze_message.html
│   ├── analyze_link.html
│   ├── analyze_screenshot.html
│   ├── analyze_job.html
│   ├── evidence.html       # Evidence locker grid
│   ├── evidence_detail.html
│   ├── complaint.html      # Complaint generator
│   ├── chatbot.html        # AI chat interface
│   ├── awareness.html      # Safety tips & guides
│   └── voice_input.html    # Voice recording UI
│
└── static/
    ├── css/
    │   └── main.css        # Cyberpunk dark theme
    └── js/
        └── main.js         # Animations, utilities, lang toggle
```

---

## 🔐 Security Notes

- All evidence is stored **locally** in SQLite — no data is sent to external servers except the AI analysis calls to OpenAI
- Upload files are stored in the local `uploads/` folder
- Complaint documents are generated server-side and never stored externally
- Use a strong `SECRET_KEY` in production

---

## 🌐 Reporting Cybercrime (India)

| Resource | Details |
|---|---|
| **National Helpline** | 1930 |
| **Portal** | https://cybercrime.gov.in |
| **Women Helpline** | 181 |
| **Emergency** | 112 |

---

## 📦 Dependencies

```
flask==3.0.3
openai==1.30.1
python-dotenv==1.0.1
pytesseract==0.3.10
Pillow==10.3.0
requests==2.32.3
werkzeug==3.0.3
flask-session==0.8.0
fpdf2==2.7.9
langdetect==1.0.9
deep-translator==1.11.4
```

---

## 🎓 Academic Project

Built as a final year BCA project demonstrating:
- Full-stack Python/Flask web development
- AI/ML integration with OpenAI API
- SQLite database design and operations
- RESTful API design
- Modern UI/UX with responsive design
- OCR and image processing
- Cybersecurity domain knowledge

---

## 📄 License

For educational and cybercrime awareness purposes only. Not for commercial use.
