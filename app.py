
from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Mushroom Cultivation Assistant</h1>
    <p>Python server is running successfully!</p>
    <p>Gemini API integration is ready for testing.</p>
    """

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
