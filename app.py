
from flask import Flask, request, jsonify, render_template_string
from google import genai
import os

app = Flask(__name__)

# Load Gemini API key from environment variable
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing!")

client = genai.Client(api_key=api_key)
HTML = """
<h1>Mushroom Cultivation Assistant</h1>

<form id="chat">
    <input id="question"
           placeholder="Ask about mushroom cultivation"
           required>
    <button>Ask</button>
</form>

<div id="answer"></div>

<script>
document.getElementById("chat").onsubmit = async function(e) {
    e.preventDefault();

    const question = document.getElementById("question").value;
    const answer = document.getElementById("answer");

    answer.innerHTML = "Thinking...";

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({question})
        });

        const data = await response.json();
        answer.innerText = data.answer || data.error;

    } catch (error) {
        answer.innerText = "Connection error.";
    }
};
</script>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ask", methods=["POST"])
def ask():
    try:
        question = request.json.get("question", "").strip()

        if not question:
            return jsonify({"error": "Please enter a question."}), 400

        prompt = f"""
        You are a mushroom cultivation assistant.
        Answer clearly and responsibly.
        Do not invent scientific information.
        If you are uncertain, say so.

        User question: {question}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return jsonify({"answer": response.text})

    except Exception as e:
        app.logger.exception("Gemini request failed")
        return jsonify({"error": "Unable to generate an answer. Check server logs."}), 500
