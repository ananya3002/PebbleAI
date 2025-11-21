# server.py
from flask import Flask, request, jsonify, send_from_directory
import re
import random
from pathlib import Path

app = Flask(__name__, static_folder="static")

# Load content files
BASE = Path(__file__).parent
def load_lines(path):
    p = BASE / path
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]

grounding = load_lines("content/grounding.md")
relaxation = load_lines("content/relaxation.md")
rules = load_lines("content/stress_detection_rules.md")
sos = load_lines("content/sos_support.md")

# Build keyword lists
low_kw = []
med_kw = []
high_kw = []
for line in rules:
    if line.lower().startswith("low keywords:"):
        low_kw = [w.strip() for w in line.split(":",1)[1].split(",")]
    if line.lower().startswith("medium keywords:"):
        med_kw = [w.strip() for w in line.split(":",1)[1].split(",")]
    if line.lower().startswith("high keywords:"):
        high_kw = [w.strip() for w in line.split(":",1)[1].split(",")]

def detect_stress(text):
    t = text.lower()
    score = 0
    # increment score for hits; high keywords weigh most
    for kw in low_kw:
        if kw and re.search(r'\b' + re.escape(kw) + r'\b', t):
            score += 1
    for kw in med_kw:
        if kw and re.search(r'\b' + re.escape(kw) + r'\b', t):
            score += 3
    for kw in high_kw:
        if kw and re.search(r'\b' + re.escape(kw) + r'\b', t):
            score += 10
    if score >= 10:
        return "high"
    if score >= 3:
        return "medium"
    return "low"

def pick_response(level):
    if level == "low":
        # suggest a tiny pause or playful prompt
        resp = random.choice(grounding) if grounding else "Try looking outside for 30 seconds and notice one color."
        tip = "Tiny pause: take one deep breath and smile."
        return f"Level: Low — {tip}\n\n{resp}"
    if level == "medium":
        resp = random.choice(relaxation) if relaxation else "Try box breathing: in 4, hold 4, out 4, hold 4."
        return f"Level: Medium — Let's try this:\n\n{resp}\n\nIf you want, do this 3 times and tell me how it felt."
    # high
    resp = "I’m really sorry you're feeling so bad. Let's do slow grounding now: "+ (random.choice(grounding) if grounding else "Try 5-4-3-2-1 grounding.")
    sos_msg = "\n\nIf you feel unsafe, please contact a trusted person or local emergency services right away."
    return f"Level: High — {resp}{sos_msg}"

@app.route("/message", methods=["POST"])
def message():
    data = request.get_json(force=True)
    text = data.get("text","")
    if not text:
        return jsonify({"error":"send JSON with a 'text' field"}), 400
    level = detect_stress(text)
    reply = pick_response(level)
    return jsonify({"level":level, "reply":reply})

# serve small UI
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True, port=7860)
