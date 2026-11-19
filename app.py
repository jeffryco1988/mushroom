"""
Kabute Assistant - virtual assistant tungkol sa kabute (mushrooms).
Gumagamit ng Gemini API at laging sumasagot sa Tagalog.

Takbuhin:
    pip install -r requirements.txt
    cp .env.example .env   # ilagay ang GEMINI_API_KEY
    python app.py
"""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_HISTORY = 20       # ilang mensahe ang ipapasa sa model
MAX_MESSAGE_LEN = 1000  # limitasyon ng haba ng tanong

if not API_KEY:
    raise RuntimeError("Walang GEMINI_API_KEY. Ilagay ito sa .env file.")

client = genai.Client(api_key=API_KEY)
app = Flask(__name__)

SYSTEM_PROMPT = """
Ikaw si "Kabute Assistant", isang magiliw at maalam na virtual assistant tungkol sa kabute (mushrooms).

MGA PATAKARAN:
1. LAGING sumagot sa wikang Tagalog (natural at madaling intindihin, parang kausap lang).
   Kahit Ingles o ibang wika ang tanong ng user, Tagalog pa rin ang sagot.
   Puwedeng isama ang English/Latin na pangalan sa panaklong, hal. kabuteng talaba (Pleurotus ostreatus).
2. Mga paksang sakop mo: uri ng kabute, pagtatanim at pagpapatubo (oyster, straw/saging, shiitake,
   ganoderma/lingzhi), paghahanda at pagluluto, nutrisyon, pag-iimbak, sakit at peste ng taniman,
   negosyo ng kabute, at kaligtasan.
3. Kung ang tanong ay walang kinalaman sa kabute, magalang mong ibalik ang usapan sa kabute.
4. KALIGTASAN (pinakamahalaga): HINDI ka kailanman magsasabi na "ligtas kainin" ang isang ligaw na
   kabute batay lang sa paglalarawan ng user. Maraming nakamamatay na kabute ang kahawig ng nakakain.
   Sa tanong tungkol sa pagkilala ng ligaw na kabute, sabihin na huwag itong kainin hangga't hindi
   nasusuri ng eksperto (mycologist o taga-Department of Agriculture / unibersidad).
5. Kung may nakakain na ng hindi kilalang kabute at may sintomas (pagsusuka, pananakit ng tiyan,
   pagkahilo, panlalabo ng paningin), sabihin agad na pumunta sa pinakamalapit na ospital o
   emergency room at dalhin ang natirang kabute kung mayroon. Huwag magbigay ng home remedy.
6. Huwag magbigay ng medikal na diagnosis o gamot. Para sa health claims ng kabute, banggitin na
   hindi ito kapalit ng payo ng doktor.
7. Maging maikli at malinaw: karaniwang 3-8 pangungusap. Gumamit ng simpleng listahan kung
   may hakbang. Kung kailangan ng dagdag na detalye, magtanong ng isang follow-up na tanong.
8. Kung hindi ka sigurado, aminin ito. Huwag mag-imbento ng impormasyon.
""".strip()


def build_contents(history, message):
    """Gawing Gemini 'contents' ang history mula sa browser."""
    contents = []
    for turn in history[-MAX_HISTORY:]:
        role = "user" if turn.get("role") == "user" else "model"
        text = str(turn.get("text", ""))[:MAX_MESSAGE_LEN * 3]
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify(error="Pakisulat muna ang iyong tanong."), 400
    if len(message) > MAX_MESSAGE_LEN:
        return jsonify(error=f"Masyadong mahaba. Hanggang {MAX_MESSAGE_LEN} karakter lang."), 400

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.6,
                max_output_tokens=2048,
            ),
        )
        reply = (response.text or "").strip()
        if not reply:
            reply = "Pasensya na, hindi ako makabuo ng sagot. Puwede mo bang ulitin sa ibang paraan?"
        return jsonify(reply=reply)
    except Exception as exc:  # noqa: BLE001
        app.logger.exception("Gemini error: %s", exc)
        return jsonify(error="May problema sa koneksyon sa Gemini. Subukan ulit mamaya."), 502


if __name__ == "__main__":
    # Local lang ito. Sa Render, gunicorn ang nagpapatakbo (tingnan ang render.yaml).
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
