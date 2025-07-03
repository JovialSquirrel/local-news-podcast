from flask import Flask, request, send_file
from generate_podcast import get_local_news, summarize_news, convert_to_audio
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Email credentials from .env
from_email = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")

# ✅ Define the Flask app BEFORE using it
app = Flask(__name__)


def send_email_with_attachment(to_email, filepath):
    msg = EmailMessage()
    msg['Subject'] = "Your Local News Podcast"
    msg['From'] = from_email
    msg['To'] = to_email
    msg.set_content("Here is your requested podcast!")

    with open(filepath, "rb") as f:
        msg.add_attachment(f.read(), maintype="audio", subtype="mpeg", filename="podcast.mp3")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(from_email, password)
        smtp.send_message(msg)


@app.route("/generate", methods=["GET"])
def generate():
    city = request.args.get("city")
    state = request.args.get("state", "")
    email = request.args.get("email")

    if not city or not email:
        return {"error": "Missing 'city' or 'email'"}, 400

    news_items = get_local_news(city, state)
    if not news_items:
        return {"error": "No news found"}, 404

    summary = summarize_news(news_items, f"{city}, {state}")
    mp3_file = convert_to_audio(summary, f"{city} {state}".strip())



    send_email_with_attachment(email, mp3_file)

    return send_file(mp3_file, mimetype="audio/mpeg")


@app.route("/")
def home():
    return '''
        <form id="podcastForm" action="/generate" method="get" style="font-family: sans-serif; padding: 2rem; max-width: 400px;">
            <label>Enter your city:</label><br>
            <input name="city" placeholder="e.g. State College" required><br><br>
            
            <label>Enter your state (optional):</label><br>
            <input name="state" placeholder="e.g. PA"><br><br>

            <label>Your email address:</label><br>
            <input name="email" type="email" placeholder="you@example.com" required><br><br>

            <button type="submit" id="submitBtn" style="padding: 0.5rem 1rem; background: #28a745; color: white; border: none;">
                Generate Podcast
            </button>
        </form>

        <script>
            const form = document.getElementById('podcastForm');
            const submitBtn = document.getElementById('submitBtn');

            form.addEventListener('submit', () => {
                submitBtn.disabled = true;
                submitBtn.innerText = "Generating...";
            });
        </script>
    '''


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

