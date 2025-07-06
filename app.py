from flask import Flask, request, send_file, render_template_string, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
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
app.secret_key = 'your-secret-key-change-this-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple User class for authentication
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hardcoded user credentials
USERS = {
    'BradGroznik': 'TheW1Z4RD@fGR0Z'
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Login page template
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>State College Podcast - Login</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            color: #333;
            margin: 0 0 0.5rem 0;
            font-size: 1.8rem;
        }
        .login-header p {
            color: #666;
            margin: 0;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .login-btn {
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.3s;
        }
        .login-btn:hover {
            background: #5a6fd8;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border: 1px solid #fcc;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>State College Podcast</h1>
            <p>Admin Login</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="login-btn">Login</button>
        </form>
    </div>
</body>
</html>
'''

# News selection template
NEWS_SELECTION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>State College Podcast - Select News</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: #f8f9fa;
            margin: 0;
            padding: 2rem;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            margin: 0;
            color: #333;
        }
        .logout-btn {
            background: #dc3545;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .logout-btn:hover {
            background: #c82333;
        }
        .news-form {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .news-item {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s;
            cursor: pointer;
        }
        .news-item:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .news-item.selected {
            border-color: #667eea;
            background: #f0f4ff;
        }
        .news-checkbox {
            margin-right: 1rem;
            transform: scale(1.2);
        }
        .news-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        .news-description {
            color: #666;
            line-height: 1.5;
        }
        .generate-btn {
            background: #28a745;
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 500;
            cursor: pointer;
            margin-top: 2rem;
            width: 100%;
            transition: background 0.3s;
        }
        .generate-btn:hover {
            background: #218838;
        }
        .generate-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .selection-counter {
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-bottom: 1rem;
            display: inline-block;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>State College Daily Podcast</h1>
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
        </div>
        
        {% if news_items %}
        <form method="post" action="{{ url_for('generate_podcast') }}" class="news-form">
            <div class="selection-counter" id="counter">0 stories selected</div>
            
            {% for item in news_items %}
            <div class="news-item" onclick="toggleSelection({{ loop.index0 }})">
                <input type="checkbox" name="selected_news" value="{{ loop.index0 }}" 
                       id="news_{{ loop.index0 }}" class="news-checkbox">
                <div class="news-content">
                    <div class="news-title">{{ item.title }}</div>
                    {% if item.description %}
                    <div class="news-description">{{ item.description }}</div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            
            <button type="submit" class="generate-btn" id="generateBtn" disabled>
                Generate Podcast with Selected Stories
            </button>
        </form>
        {% else %}
        <div class="news-form">
            <div class="loading">
                <h3>No news articles found for State College, PA</h3>
                <p>Please try again later or check your API configuration.</p>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        function toggleSelection(index) {
            const checkbox = document.getElementById('news_' + index);
            const newsItem = checkbox.closest('.news-item');
            
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                newsItem.classList.add('selected');
            } else {
                newsItem.classList.remove('selected');
            }
            
            updateCounter();
        }
        
        function updateCounter() {
            const checkboxes = document.querySelectorAll('input[name="selected_news"]:checked');
            const count = checkboxes.length;
            const counter = document.getElementById('counter');
            const generateBtn = document.getElementById('generateBtn');
            
            counter.textContent = count + ' stories selected';
            generateBtn.disabled = count === 0;
        }
        
        // Initialize counter on page load
        updateCounter();
    </script>
</body>
</html>
'''

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username in USERS and USERS[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('select_news'))
        else:
            flash('Invalid username or password')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def home():
    return redirect(url_for('select_news'))

@app.route("/select-news")
@login_required
def select_news():
    # Get news for State College, PA with increased limit
    news_items = get_local_news("State College", "PA", limit=20)
    
    # Convert to objects with title and description for template
    news_objects = []
    for item in news_items:
        # Split the item into title and description
        parts = item.split('. ', 1)
        title = parts[0]
        description = parts[1] if len(parts) > 1 else ""
        news_objects.append({'title': title, 'description': description})
    
    return render_template_string(NEWS_SELECTION_TEMPLATE, news_items=news_objects)

@app.route("/generate-podcast", methods=["POST"])
@login_required
def generate_podcast():
    selected_indices = request.form.getlist('selected_news')
    
    if not selected_indices:
        flash('Please select at least one news story')
        return redirect(url_for('select_news'))
    
    # Get all news items again
    all_news = get_local_news("State College", "PA", limit=20)
    
    # Filter selected news items
    selected_news = [all_news[int(i)] for i in selected_indices]
    
    # Generate podcast
    summary = summarize_news(selected_news, "State College, PA")
    mp3_file = convert_to_audio(summary, "State College PA")
    
    return send_file(mp3_file, mimetype="audio/mpeg", as_attachment=True)

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

# Keep the old generate route for backward compatibility if needed
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)