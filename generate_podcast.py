import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# API Keys
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("Missing ElevenLabs API key")




def get_local_news(city, state=""):
    query = f"{city} {state}" if state else city
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={query}&country=us&language=en&category=top"
    logging.info(f"Requesting news for: {query}")
    logging.info(f"URL: {url}")
    response = requests.get(url)
    logging.info(f"NewsData API status: {response.status_code}")
    logging.info(f"NewsData API response: {response.text}")

    data = response.json()
    articles = data.get("results", [])[:5]

    if not articles:
        logging.warning("No articles found")
        return []

    return [f"{a['title']}. {a['description'] or ''}" for a in articles]


def summarize_news(news_items, city_name):
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError("Missing OpenRouter API key.")

    news_text = "\n".join([f"{i+1}. {story}" for i, story in enumerate(news_items)])

    prompt = f"""
You are a friendly podcast host. Using ONLY the news stories below, create a detailed 7-10 minute spoken script summarizing ALL the important local news for listeners in {city_name}.

Make sure to cover EACH news story in the list clearly and completely. Do NOT skip any.

Do NOT include any commentary, analysis, or meta text — only the words to be said in the podcast.

Write in a casual, engaging tone, like you’re speaking directly to listeners.

News stories:
{chr(10).join(news_items)}

End the script naturally.
"""


    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "anthropic/claude-3-sonnet",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        logging.info(f"Claude API raw response: {result}")
        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error from Claude: {e}")
        return "Sorry, there was a problem contacting the Claude API. Try again later."

    except KeyError:
        logging.error(f"Unexpected response format from Claude: {response.text}")
        return "Sorry, something went wrong formatting the Claude response."


from datetime import datetime

import re
from datetime import datetime

def sanitize_filename(name):
    # Replace anything that's not a letter, number, space, or hyphen with nothing
    name = re.sub(r"[^\w\s-]", "", name)
    # Replace spaces with underscores
    return name.replace(" ", "_")

from gtts import gTTS
from datetime import datetime
import re

def convert_to_audio(text, location_name):
    # Sanitize file name
    today = datetime.now().strftime("%A, %B %d")
    safe_location = re.sub(r'[\\/*?:"<>|]', "", location_name)
    filename = f"{safe_location} News {today}.mp3"

    tts = gTTS(text)
    tts.save(filename)

    return filename






# Log keys info (partially masked)
logging.info(f"Using NewsData API key: {NEWSDATA_API_KEY[:5]}...{NEWSDATA_API_KEY[-4:]}")
logging.info(f"Using ElevenLabs API key: {ELEVENLABS_API_KEY[:5]}...{ELEVENLABS_API_KEY[-4:]}")
