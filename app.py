# ============================================================
# AI-Based Smart Forensic Intelligence System
# app.py — Main Flask Application
# ============================================================

import os
import json
import sqlite3
import uuid
import base64
import re
import hashlib
from datetime import datetime
from io import BytesIO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, g
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Optional imports (graceful degradation) ─────────────────
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

# ── App Configuration ────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "forensiq-secret-2024")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "dummy")

# ── Database Path ────────────────────────────────────────────
DB_PATH = os.path.join("database", "forensiq.db")
os.makedirs("database", exist_ok=True)
os.makedirs("uploads", exist_ok=True)


# ════════════════════════════════════════════════════════════
#  DATABASE SETUP
# ════════════════════════════════════════════════════════════

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    cursor = db.cursor()

    # Users table — NEW
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT NOT NULL,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created       TEXT NOT NULL
        )
    """)

    # Evidence locker
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ev_id     TEXT UNIQUE NOT NULL,
            type      TEXT NOT NULL,
            content   TEXT NOT NULL,
            result    TEXT NOT NULL,
            risk      INTEGER DEFAULT 0,
            details   TEXT,
            actions   TEXT,
            language  TEXT DEFAULT 'en',
            created   TEXT NOT NULL
        )
    """)

    # Chat history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            role     TEXT NOT NULL,
            message  TEXT NOT NULL,
            created  TEXT NOT NULL
        )
    """)

    # Scam patterns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scam_patterns (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            pattern  TEXT NOT NULL,
            keywords TEXT NOT NULL
        )
    """)

    db.commit()

    cursor.execute("SELECT COUNT(*) FROM scam_patterns")
    if cursor.fetchone()[0] == 0:
        _seed_scam_patterns(cursor)
        db.commit()

    db.close()


def _seed_scam_patterns(cursor):
    patterns = [
        ("Lottery Scam",        "You have won a lottery prize. Claim now by sending fee.",
         "won,lottery,prize,claim,fee,congratulations,winner"),
        ("Bank Phishing",       "Your account has been suspended. Verify now at our secure link.",
         "account,suspended,verify,secure,bank,login,OTP"),
        ("Job Scam",            "Work from home and earn 50000 per day. No experience needed.",
         "work from home,earn,per day,no experience,easy money,part time"),
        ("Investment Fraud",    "Double your investment in 24 hours. Guaranteed returns.",
         "invest,double,guaranteed,returns,profit,24 hours,crypto"),
        ("KYC Fraud",           "Your KYC is incomplete. Update immediately to avoid account block.",
         "KYC,incomplete,update,block,immediately,Aadhaar,PAN"),
        ("Tech Support Scam",   "Your computer is infected. Call Microsoft support immediately.",
         "infected,virus,Microsoft,support,call,remote,access"),
        ("Romance Scam",        "I am a military officer stranded. Please send money for return.",
         "military,stranded,money,love,send,transfer,stuck"),
        ("Courier Scam",        "Your parcel is on hold. Pay customs duty to release.",
         "parcel,courier,customs,duty,hold,release,delivery"),
        ("Phishing Email",      "Click this link to reset your password or your account will be deleted.",
         "click,link,password,reset,delete,account,urgent"),
        ("Advance Fee Fraud",   "You are selected for inheritance. Pay processing fee to claim.",
         "inheritance,selected,fee,processing,claim,amount,transfer"),
        ("Fake Job Offer",      "Hired! Send joining fee to confirm your position in MNC.",
         "hired,joining fee,MNC,position,confirm,salary,offer letter"),
        ("Sextortion",          "We have recorded you. Pay or we will send video to contacts.",
         "recorded,video,pay,contacts,send,camera,expose"),
    ]
    for cat, patt, kw in patterns:
        cursor.execute(
            "INSERT INTO scam_patterns (category, pattern, keywords) VALUES (?,?,?)",
            (cat, patt, kw)
        )


# ════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ════════════════════════════════════════════════════════════

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in app.config["ALLOWED_EXTENSIONS"]
    )


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gen_id():
    return uuid.uuid4().hex[:12].upper()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def save_evidence(type_, content, result, risk, details, actions, language="en"):
    db = get_db()
    ev_id = gen_id()
    db.execute(
        """INSERT INTO evidence
           (ev_id,type,content,result,risk,details,actions,language,created)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (ev_id, type_, content[:2000], result, risk,
         json.dumps(details), json.dumps(actions), language, timestamp())
    )
    db.commit()
    db.close()
    return ev_id


# ── Login required decorator ─────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Groq / AI helper ─────────────────────────────────────────

def call_openai(system_prompt: str, user_prompt: str,
                model: str = "llama-3.3-70b-versatile",
                max_tokens: int = 800) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return json.dumps({
            "verdict": "SUSPICIOUS",
            "risk_score": 50,
            "category": "Unknown",
            "explanation": f"AI analysis unavailable: {exc}",
            "red_flags": [],
            "actions": ["Verify the content manually.", "Contact authorities if in doubt."]
        })


def _mock_ai_response(text: str) -> str:
    text_lower = text.lower()
    scam_keywords = [
        "won", "lottery", "prize", "claim", "verify", "otp",
        "suspended", "urgent", "click here", "password", "bank",
        "invest", "double", "guaranteed", "kyc", "aadhaar",
        "earn", "per day", "work from home", "free", "lucky",
        "congratulations", "winner", "account blocked", "customs",
        "joining fee", "hired", "naked", "video", "bitcoin",
        "crypto", "wire transfer", "western union",
    ]
    hits = [kw for kw in scam_keywords if kw in text_lower]
    if len(hits) >= 3:
        verdict = "SCAM"
        risk = min(90, 50 + len(hits) * 8)
        explanation = (
            f"⚠️ HIGH RISK detected. Found {len(hits)} suspicious keywords: "
            + ", ".join(hits[:5])
            + ". This strongly resembles a known scam pattern."
        )
        actions = [
            "Do NOT click any links in this message.",
            "Do NOT share personal or financial information.",
            "Report this to cybercrime.gov.in or call 1930.",
            "Block the sender immediately.",
        ]
    elif len(hits) >= 1:
        verdict = "SUSPICIOUS"
        risk = min(60, 30 + len(hits) * 10)
        explanation = (
            f"⚡ SUSPICIOUS content. Found keyword(s): "
            + ", ".join(hits)
            + ". Proceed with caution."
        )
        actions = [
            "Verify the sender's identity through official channels.",
            "Do not share OTPs or passwords.",
            "Cross-check any links before clicking.",
        ]
    else:
        verdict = "SAFE"
        risk = 10
        explanation = "✅ No obvious threat patterns detected. Always stay cautious online."
        actions = [
            "Content appears safe but stay vigilant.",
            "Keep your devices and software updated.",
        ]
    return json.dumps({
        "verdict": verdict,
        "risk_score": risk,
        "explanation": explanation,
        "actions": actions,
        "category": "Heuristic Analysis",
    })


# ── Scam similarity checker ──────────────────────────────────

def find_similar_scams(text: str) -> list[dict]:
    db = get_db()
    patterns = db.execute(
        "SELECT category, pattern, keywords FROM scam_patterns"
    ).fetchall()
    db.close()

    text_lower = text.lower()
    matches = []
    for row in patterns:
        kws = [k.strip().lower() for k in row["keywords"].split(",")]
        hit_count = sum(1 for k in kws if k in text_lower)
        if hit_count >= 2:
            matches.append({
                "category":    row["category"],
                "pattern":     row["pattern"],
                "match_score": round(hit_count / len(kws) * 100),
            })
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches[:3]


# ── Core AI Analysis ─────────────────────────────────────────

SYSTEM_FORENSIC = """You are an expert cyber-forensics AI.
Analyse the provided content and respond ONLY with valid JSON in this exact schema:
{
  "verdict": "SAFE | SUSPICIOUS | SCAM | PHISHING | FRAUD",
  "risk_score": <integer 0-100>,
  "category": "<type of threat or 'Benign'>",
  "explanation": "<2-3 sentences plain-English explanation>",
  "red_flags": ["<flag1>", "<flag2>"],
  "actions": ["<action1>", "<action2>", "<action3>"]
}
Be precise and helpful for non-technical users."""


def parse_ai_json(raw: str) -> dict:
    raw = re.sub(r"```(?:json)?", "", raw).strip("` \n")
    try:
        return json.loads(raw)
    except Exception:
        return {
            "verdict": "SUSPICIOUS",
            "risk_score": 50,
            "category": "Unknown",
            "explanation": raw[:300],
            "red_flags": [],
            "actions": ["Verify the content manually.", "Contact authorities if in doubt."],
        }


def analyze_text(content: str) -> dict:
    raw = call_openai(SYSTEM_FORENSIC, f"Analyse this message:\n\n{content}")
    return parse_ai_json(raw)


def analyze_url(url: str) -> dict:
    raw = call_openai(SYSTEM_FORENSIC, f"Analyse this URL for phishing, malware, or fraud:\n\n{url}")
    return parse_ai_json(raw)


def analyze_job(content: str) -> dict:
    raw = call_openai(SYSTEM_FORENSIC, f"Analyse this job offer or employment-related message for scams:\n\n{content}")
    return parse_ai_json(raw)


# ════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("login"))

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? OR email=?",
            (username, username)
        ).fetchone()
        db.close()

        if user and user["password_hash"] == hash_password(password):
            session["user_id"]   = user["id"]
            session["username"]  = user["username"]
            session["full_name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}! 👋", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name        = request.form.get("full_name", "").strip()
        username         = request.form.get("username", "").strip()
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validations
        if not all([full_name, username, email, password, confirm_password]):
            flash("Please fill in all fields.", "warning")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("signup"))

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username=? OR email=?",
            (username, email)
        ).fetchone()

        if existing:
            db.close()
            flash("Username or email already exists.", "danger")
            return redirect(url_for("signup"))

        db.execute(
            "INSERT INTO users (full_name, username, email, password_hash, created) VALUES (?,?,?,?,?)",
            (full_name, username, email, hash_password(password), timestamp())
        )
        db.commit()
        db.close()

        flash("Account created successfully! Please login. 🎉", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ════════════════════════════════════════════════════════════
#  MAIN ROUTES
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    scams = db.execute(
        "SELECT COUNT(*) FROM evidence WHERE result IN ('SCAM','PHISHING','FRAUD')"
    ).fetchone()[0]
    db.close()
    return render_template("index.html", total=total, scams_blocked=scams)


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    recent = db.execute(
        "SELECT * FROM evidence ORDER BY created DESC LIMIT 8"
    ).fetchall()
    counts = {
        "total":      db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0],
        "scam":       db.execute("SELECT COUNT(*) FROM evidence WHERE result='SCAM'").fetchone()[0],
        "phishing":   db.execute("SELECT COUNT(*) FROM evidence WHERE result='PHISHING'").fetchone()[0],
        "fraud":      db.execute("SELECT COUNT(*) FROM evidence WHERE result='FRAUD'").fetchone()[0],
        "safe":       db.execute("SELECT COUNT(*) FROM evidence WHERE result='SAFE'").fetchone()[0],
        "suspicious": db.execute("SELECT COUNT(*) FROM evidence WHERE result='SUSPICIOUS'").fetchone()[0],
    }
    db.close()
    return render_template("dashboard.html", recent=recent, counts=counts)


# ── Message Analyzer ─────────────────────────────────────────

@app.route("/analyze/message", methods=["GET", "POST"])
@login_required
def analyze_message():
    result = None
    similar = []
    if request.method == "POST":
        content  = request.form.get("message", "").strip()
        language = request.form.get("language", "en")
        if not content:
            flash("Please enter a message to analyse.", "warning")
            return redirect(url_for("analyze_message"))

        analysis = analyze_text(content)
        similar  = find_similar_scams(content)
        ev_id    = save_evidence(
            "message", content,
            analysis["verdict"], analysis["risk_score"],
            analysis, analysis.get("actions", []),
            language
        )
        result = {**analysis, "ev_id": ev_id, "similar": similar}
    return render_template("analyze_message.html", result=result)


# ── Link Checker ─────────────────────────────────────────────

@app.route("/analyze/link", methods=["GET", "POST"])
@login_required
def analyze_link():
    result = None
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            flash("Please enter a URL.", "warning")
            return redirect(url_for("analyze_link"))

        heuristics = []
        suspicious_tlds = [".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".click"]
        if any(url.lower().endswith(t) or t + "/" in url.lower() for t in suspicious_tlds):
            heuristics.append("Suspicious TLD detected")
        if len(url) > 100:
            heuristics.append("Unusually long URL")
        if url.count("-") > 4:
            heuristics.append("Excessive hyphens (common in phishing)")
        if re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url):
            heuristics.append("IP address used instead of domain name")

        extra = (" Additional heuristic flags: " + "; ".join(heuristics)) if heuristics else ""
        analysis = analyze_url(url + extra)
        ev_id = save_evidence(
            "link", url,
            analysis["verdict"], analysis["risk_score"],
            analysis, analysis.get("actions", [])
        )
        result = {**analysis, "ev_id": ev_id, "heuristics": heuristics}
    return render_template("analyze_link.html", result=result)


# ── Screenshot Analyzer ──────────────────────────────────────

@app.route("/analyze/screenshot", methods=["GET", "POST"])
@login_required
def analyze_screenshot():
    result   = None
    ocr_text = ""
    if request.method == "POST":
        if "screenshot" not in request.files:
            flash("No file uploaded.", "warning")
            return redirect(url_for("analyze_screenshot"))

        file = request.files["screenshot"]
        if file.filename == "":
            flash("No file selected.", "warning")
            return redirect(url_for("analyze_screenshot"))

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{gen_id()}_{file.filename}")
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            if OCR_AVAILABLE:
                try:
                    img      = Image.open(filepath)
                    ocr_text = pytesseract.image_to_string(img).strip()
                except Exception as e:
                    ocr_text = f"[OCR Error: {e}]"
            else:
                ocr_text = "[OCR not available]"

            analyse_input = ocr_text if ocr_text and not ocr_text.startswith("[") \
                else "Image uploaded but OCR extraction failed."

            analysis = analyze_text(analyse_input)
            similar  = find_similar_scams(analyse_input)
            ev_id    = save_evidence(
                "screenshot", ocr_text[:1000] or filename,
                analysis["verdict"], analysis["risk_score"],
                analysis, analysis.get("actions", [])
            )
            result = {**analysis, "ev_id": ev_id, "ocr_text": ocr_text,
                      "similar": similar, "filename": filename}
        else:
            flash("Invalid file type. Upload PNG, JPG, or GIF.", "danger")
    return render_template("analyze_screenshot.html", result=result, ocr_text=ocr_text)


# ── Job/Offer Detector ───────────────────────────────────────

@app.route("/analyze/job", methods=["GET", "POST"])
@login_required
def analyze_job_offer():
    result  = None
    similar = []
    if request.method == "POST":
        content = request.form.get("job_text", "").strip()
        if not content:
            flash("Please enter the job offer text.", "warning")
            return redirect(url_for("analyze_job_offer"))

        analysis = analyze_job(content)
        similar  = find_similar_scams(content)
        ev_id    = save_evidence(
            "job", content,
            analysis["verdict"], analysis["risk_score"],
            analysis, analysis.get("actions", [])
        )
        result = {**analysis, "ev_id": ev_id, "similar": similar}
    return render_template("analyze_job.html", result=result)


# ── Evidence Locker ──────────────────────────────────────────

@app.route("/evidence")
@login_required
def evidence_locker():
    db   = get_db()
    page = int(request.args.get("page", 1))
    per  = 12
    off  = (page - 1) * per
    items = db.execute(
        "SELECT * FROM evidence ORDER BY created DESC LIMIT ? OFFSET ?",
        (per, off)
    ).fetchall()
    total = db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
    db.close()
    pages = (total + per - 1) // per
    return render_template("evidence.html", items=items, page=page, pages=pages, total=total)


@app.route("/evidence/delete/<ev_id>", methods=["POST"])
@login_required
def delete_evidence(ev_id):
    db = get_db()
    db.execute("DELETE FROM evidence WHERE ev_id=?", (ev_id,))
    db.commit()
    db.close()
    flash("Evidence record deleted.", "info")
    return redirect(url_for("evidence_locker"))


@app.route("/evidence/view/<ev_id>")
@login_required
def view_evidence(ev_id):
    db   = get_db()
    item = db.execute("SELECT * FROM evidence WHERE ev_id=?", (ev_id,)).fetchone()
    db.close()
    if not item:
        flash("Evidence not found.", "danger")
        return redirect(url_for("evidence_locker"))
    details = json.loads(item["details"]) if item["details"] else {}
    actions = json.loads(item["actions"]) if item["actions"] else []
    return render_template("evidence_detail.html", item=item, details=details, actions=actions)


# ── Complaint Generator ──────────────────────────────────────

@app.route("/complaint/<ev_id>")
@login_required
def generate_complaint(ev_id):
    db   = get_db()
    item = db.execute("SELECT * FROM evidence WHERE ev_id=?", (ev_id,)).fetchone()
    db.close()
    if not item:
        flash("Evidence not found.", "danger")
        return redirect(url_for("evidence_locker"))

    details = json.loads(item["details"]) if item["details"] else {}
    actions = json.loads(item["actions"]) if item["actions"] else []

    prompt = (
        f"Generate a formal cybercrime complaint for:\n"
        f"Type: {item['type']}\nContent: {item['content'][:500]}\n"
        f"Verdict: {item['result']}\nRisk: {item['risk']}/100\n"
        f"Details: {details.get('explanation','')}\n"
        "Write a professional complaint in 150-200 words suitable for submission "
        "to cybercrime.gov.in or a police station. Include placeholders for "
        "victim name and contact."
    )
    complaint_text = call_openai(
        "You are a legal assistant helping cybercrime victims draft formal complaints.",
        prompt, max_tokens=400
    )
    return render_template(
        "complaint.html",
        item=item, details=details, actions=actions,
        complaint_text=complaint_text
    )


# ── AI Chatbot ───────────────────────────────────────────────

@app.route("/chatbot")
@login_required
def chatbot():
    db      = get_db()
    history = db.execute(
        "SELECT role, message, created FROM chat_history ORDER BY created DESC LIMIT 20"
    ).fetchall()
    db.close()
    history = list(reversed(history))
    return render_template("chatbot.html", history=history)


@app.route("/chatbot/send", methods=["POST"])
@login_required
def chatbot_send():
    data    = request.get_json()
    message = (data or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    system = (
        "You are CyberGuard AI, a friendly cyber-safety assistant. "
        "Help users understand cyber threats, scams, phishing, and digital safety. "
        "Keep answers concise (3-5 sentences), friendly, and actionable."
    )
    reply = call_openai(system, message, max_tokens=300)

    db = get_db()
    db.execute("INSERT INTO chat_history (role,message,created) VALUES (?,?,?)",
               ("user", message, timestamp()))
    db.execute("INSERT INTO chat_history (role,message,created) VALUES (?,?,?)",
               ("assistant", reply, timestamp()))
    db.commit()
    db.close()
    return jsonify({"reply": reply})


@app.route("/chatbot/clear", methods=["POST"])
@login_required
def chatbot_clear():
    db = get_db()
    db.execute("DELETE FROM chat_history")
    db.commit()
    db.close()
    return jsonify({"status": "cleared"})


# ── Awareness ────────────────────────────────────────────────

@app.route("/awareness")
@login_required
def awareness():
    ai_tips = call_openai(
        "You are a cybersecurity educator.",
        "Give 8 practical, numbered cybersecurity tips for everyday internet users. "
        "Each tip should be 1-2 sentences. No markdown headers, just numbered list.",
        max_tokens=500
    )
    tips_list = [t.strip() for t in ai_tips.split("\n") if t.strip()]
    return render_template("awareness.html", ai_tips=tips_list)


# ── Translate API ────────────────────────────────────────────

@app.route("/api/translate", methods=["POST"])
def translate_text():
    data   = request.get_json()
    text   = (data or {}).get("text", "")
    target = (data or {}).get("target", "hi")

    if not TRANSLATE_AVAILABLE:
        return jsonify({"translated": text, "note": "Translation library not available."})
    try:
        translated = GoogleTranslator(source="auto", target=target).translate(text)
        return jsonify({"translated": translated})
    except Exception as e:
        return jsonify({"translated": text, "error": str(e)})


# ── Voice Input ──────────────────────────────────────────────

@app.route("/analyze/voice")
@login_required
def voice_input():
    return render_template("voice_input.html")


# ── Stats API ────────────────────────────────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    by_result = db.execute("SELECT result, COUNT(*) as c FROM evidence GROUP BY result").fetchall()
    by_type   = db.execute("SELECT type, COUNT(*) as c FROM evidence GROUP BY type").fetchall()
    daily     = db.execute(
        """SELECT DATE(created) as d, COUNT(*) as c
           FROM evidence
           WHERE created >= DATE('now','-7 days')
           GROUP BY DATE(created) ORDER BY d"""
    ).fetchall()
    db.close()
    return jsonify({
        "by_result": {r["result"]: r["c"] for r in by_result},
        "by_type":   {r["type"]:   r["c"] for r in by_type},
        "daily":     [{"date": r["d"], "count": r["c"]} for r in daily],
    })


# ════════════════════════════════════════════════════════════
#  APP STARTUP
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    with app.app_context():
        init_db()
    print("=" * 55)
    print(" 🔍 Smart Forensic Intelligence — Running")
    print(f"    OpenAI:  {'✅ Connected' if True else '⚠️  Demo mode'}")
    print(f"    OCR:     {'✅ Available' if OCR_AVAILABLE else '⚠️  Not installed'}")
    print(f"    PDF:     {'✅ Available' if PDF_AVAILABLE else '⚠️  Not installed'}")
    print("    URL:     http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=os.getenv("FLASK_DEBUG", "True") == "True", port=5000)
