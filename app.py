import os
import sys
import json
import urllib.request
import urllib.parse
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from detection.sld import (
    load_sld_content_bank,
    analyze_tier1_data,
    analyze_tier2_data,
    analyze_tier3_data,
    analyze_tier4_data
)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.environ.get("SECRET_KEY", "sanket-sld-secret-key-2026")


# ── PAGE ROUTES ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

@app.route("/test/sld")
def sld_hub():
    return render_template("sld/hub.html")

@app.route("/test/sld/tier1")
def sld_tier1():
    return render_template("sld/tier1.html")

@app.route("/test/sld/tier2")
def sld_tier2():
    return render_template("sld/tier2.html")

@app.route("/test/sld/tier3")
def sld_tier3():
    return render_template("sld/tier3.html")

@app.route("/test/sld/tier4")
def sld_tier4():
    return render_template("sld/tier4.html")

@app.route("/test/sld/results")
def sld_results():
    return render_template("sld/results.html")


# ── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route("/api/sld/content/<int:tier_num>", methods=["GET"])
def api_sld_content(tier_num):
    try:
        lang = request.args.get("lang", "en")
        content, fallback = load_sld_content_bank(lang, tier_num)
        return jsonify({"content": content, "fallback": fallback, **content})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/sld/analyze/tier1", methods=["POST"])
def api_sld_analyze_tier1():
    try:
        data = request.get_json()
        rhyme = data.get("rhyme_results", [])
        subitizing = data.get("subitizing_results", [])
        motor = data.get("motor_results", {})
        res = analyze_tier1_data(rhyme, subitizing, motor)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/sld/analyze/tier2", methods=["POST"])
def api_sld_analyze_tier2():
    try:
        data = request.get_json()
        dyslexia = data.get("dyslexia", {})
        dyscalculia = data.get("dyscalculia", {})
        dysgraphia = data.get("dysgraphia", {})
        res = analyze_tier2_data(dyslexia, dyscalculia, dysgraphia)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/sld/analyze/tier3", methods=["POST"])
def api_sld_analyze_tier3():
    try:
        data = request.get_json()
        ran = data.get("ran_multi_round", {})
        decoding = data.get("adaptive_decoding", {})
        decay = data.get("sight_word_decay", {})
        comp = data.get("long_comprehension", {})
        dyscalculia = data.get("dyscalculia", {})
        dysgraphia = data.get("dysgraphia", {})
        res = analyze_tier3_data(ran, decoding, decay, comp, dyscalculia, dysgraphia)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/sld/analyze/tier4", methods=["POST"])
def api_sld_analyze_tier4():
    try:
        data = request.get_json()
        distress = data.get("distress_answers", {})
        cog = data.get("cognitive_data", {})
        res = analyze_tier4_data(distress, cog)
        return jsonify(res)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

@app.route("/api/translate", methods=["POST"])
def api_translate():
    try:
        req_data = request.get_json() or {}
        text = req_data.get("text", "")
        target_lang = req_data.get("target_lang", "en")
        
        if not text or target_lang == "en":
            return jsonify({"translated_text": text})
            
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            translated_text = "".join([part[0] for part in res_json[0] if part[0]])
            return jsonify({"translated_text": translated_text})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"translated_text": req_data.get("text", ""), "error": str(e)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
